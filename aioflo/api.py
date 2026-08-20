"""Define a base client for interacting with Flo."""
from datetime import datetime, timedelta
import logging
from typing import Optional
from urllib.parse import urlparse

from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from .alarm import Alarm
from .const import API_V2_BASE
from .device import Device
from .errors import RequestError
from .location import Location
from .presence import Presence
from .user import User
from .water import Water

_LOGGER = logging.getLogger(__name__)

API_V1_BASE: str = "https://api.meetflo.com/api/v1"

# Moen SSO (Cognito). This is the auth the current Moen Smartwater app uses. The legacy
# ``users/auth`` flow above still works, so this is opt-in cover for that endpoint being
# retired rather than a fix for a live breakage.
SSO_TOKEN_URL: str = (
    "https://4j1gkf0vji.execute-api.us-east-2.amazonaws.com/prod/v1/oauth2/token"
)
SSO_CLIENT_ID: str = "6qn9pep31dglq6ed4fvlq6rp5t"
# Refresh this many seconds before the token actually expires, so a request in flight
# does not race the expiry.
SSO_EXPIRY_MARGIN: int = 60

DEFAULT_HEADER_ACCEPT: str = "application/json, text/plain, */*"
DEFAULT_HEADER_CONTENT_TYPE: str = "application/json;charset=UTF-8"
DEFAULT_HEADER_ORIGIN: str = "https://user.meetflo.com"
DEFAULT_HEADER_REFERER: str = "https://user.meetflo.com/home"
DEFAULT_HEADER_USER_AGENT: str = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36"
)
DEFAULT_TIMEOUT: int = 10


class API:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Define the API object."""

    def __init__(
        self,
        username: str,
        password: str,
        *,
        session: Optional[ClientSession] = None,
        use_sso: bool = False,
    ) -> None:
        """Initialize.

        :param use_sso: Authenticate via the Moen SSO (Cognito) flow instead of the
            legacy Flo ``users/auth`` flow.
        :type use_sso: ``bool``
        """
        self._password: str = password
        self._session: ClientSession = session
        self._token: Optional[str] = None
        self._token_expiration: Optional[datetime] = None
        self._refresh_token: Optional[str] = None
        self._use_sso: bool = use_sso
        self._user_id: Optional[str] = None
        self._username: str = username

        self.alarm: Alarm = Alarm(self._request)
        self.location: Location = Location(self._request)
        self.water: Water = Water(self._request)
        self.device: Device = Device(self._request)
        self.presence: Presence = Presence(self._request)

        # These endpoints will get instantiated post-authentication:
        self.user: Optional[User] = None

    async def _request(  # pylint: disable=too-many-locals
        self,
        method: str,
        url: str,
        *,
        _allow_reauth: bool = True,
        _anonymous: bool = False,
        **kwargs,
    ) -> dict:
        """Make a request against the API."""
        if self._token_expiration and datetime.now() >= self._token_expiration:
            _LOGGER.info("Requesting new access token to replace expired one")

            # Nullify the token so that the authentication request doesn't use it:
            self._token = None

            # Nullify the expiration so the authentication request doesn't get caught
            # here:
            self._token_expiration = None

            if self._use_sso:
                await self._async_refresh_sso()
            else:
                await self.async_authenticate()

        kwargs.setdefault("headers", {})
        kwargs["headers"].update(
            {
                "Accept": DEFAULT_HEADER_ACCEPT,
                "Content-Type": DEFAULT_HEADER_CONTENT_TYPE,
                "Host": urlparse(url).netloc,
                "Origin": DEFAULT_HEADER_ORIGIN,
                "Referrer": DEFAULT_HEADER_REFERER,
                "User-Agent": DEFAULT_HEADER_USER_AGENT,
            }
        )

        if self._token and not _anonymous:
            kwargs["headers"]["Authorization"] = (
                f"Bearer {self._token}" if self._use_sso else self._token
            )

        use_running_session = self._session and not self._session.closed

        if use_running_session:
            session = self._session
        else:
            session = ClientSession(timeout=ClientTimeout(total=DEFAULT_TIMEOUT))

        try:
            async with session.request(method, url, **kwargs) as resp:
                # An SSO access token can be rejected before its nominal expiry (for
                # example after a password change elsewhere). Refresh once and retry
                # rather than surfacing a 401 to the caller.
                if (
                    resp.status == 401
                    and self._use_sso
                    and _allow_reauth
                    and self._token is not None
                ):
                    _LOGGER.info("Access token rejected; refreshing and retrying")
                else:
                    resp.raise_for_status()
                    data: dict = await resp.json(content_type=None)
                    return data
        except ClientError as err:
            raise RequestError(f"There was an error while requesting {url}") from err
        finally:
            if not use_running_session:
                await session.close()

        # Only reachable on a 401 from the SSO path:
        await self._async_refresh_sso()
        return await self._request(method, url, _allow_reauth=False, **kwargs)

    async def async_authenticate(self) -> None:
        """Authenticate the user and set the access token with its expiration."""
        if self._use_sso:
            await self._async_authenticate_sso()
        else:
            await self._async_authenticate_legacy()

    async def _async_authenticate_legacy(self) -> None:
        """Authenticate via the legacy Flo ``users/auth`` flow."""
        auth_response: dict = await self._request(
            "post",
            f"{API_V1_BASE}/users/auth",
            json={"username": self._username, "password": self._password},
        )

        self._token = auth_response["token"]
        self._token_expiration = datetime.fromtimestamp(
            auth_response["tokenPayload"]["timestamp"]
            + auth_response["tokenExpiration"]
        )

        if not self._user_id:
            self._user_id = auth_response["tokenPayload"]["user"]["user_id"]
            assert self._user_id
            self.user = User(self._request, self._user_id)

    async def _async_sso_token_request(self, payload: dict) -> dict:
        """Post to the SSO token endpoint and return the token object."""
        response: dict = await self._request(
            "post",
            SSO_TOKEN_URL,
            json={**payload, "client_id": SSO_CLIENT_ID},
            _allow_reauth=False,
            _anonymous=True,
        )
        # The endpoint nests the token; tolerate a flat response too.
        token: dict = response.get("token", response)
        if "access_token" not in token:
            raise RequestError("SSO login returned no access token")
        return token

    def _store_sso_token(self, token: dict) -> None:
        """Record an SSO token and when it needs replacing."""
        self._token = token["access_token"]
        # A refresh-grant response may omit the refresh token; keep the existing one.
        self._refresh_token = token.get("refresh_token", self._refresh_token)
        self._token_expiration = datetime.now() + timedelta(
            seconds=int(token.get("expires_in", 3600)) - SSO_EXPIRY_MARGIN
        )

    async def _async_authenticate_sso(self) -> None:
        """Authenticate via the Moen SSO (Cognito) flow."""
        token = await self._async_sso_token_request(
            {"username": self._username, "password": self._password}
        )
        self._store_sso_token(token)

        if not self._user_id:
            # Unlike the legacy token, the SSO token does not embed the user id.
            me: dict = await self._request(
                "get", f"{API_V2_BASE}/users/me", _allow_reauth=False
            )
            self._user_id = me["id"]
            assert self._user_id
            self.user = User(self._request, self._user_id)

    async def _async_refresh_sso(self) -> None:
        """Exchange the refresh token, falling back to a full login."""
        if not self._refresh_token:
            await self._async_authenticate_sso()
            return

        try:
            token = await self._async_sso_token_request(
                {"grant_type": "refresh_token", "refresh_token": self._refresh_token}
            )
        except RequestError:
            _LOGGER.info("Refresh token rejected; falling back to a full login")
            self._refresh_token = None
            await self._async_authenticate_sso()
            return

        self._store_sso_token(token)


async def async_get_api(
    username: str,
    password: str,
    *,
    session: Optional[ClientSession] = None,
    use_sso: bool = False,
) -> API:
    """Instantiate an authenticated API object.

    :param session: An ``aiohttp`` ``ClientSession``
    :type session: ``aiohttp.client.ClientSession``
    :param email: A Flo email address
    :type email: ``str``
    :param password: A Flo password
    :type password: ``str``
    :param use_sso: Use the Moen SSO (Cognito) auth flow instead of the legacy one
    :type use_sso: ``bool``
    :rtype: :meth:`aioflo.api.API`
    """
    api = API(username, password, session=session, use_sso=use_sso)
    await api.async_authenticate()
    return api
