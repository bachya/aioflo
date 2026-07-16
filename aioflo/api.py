"""Define a base client for interacting with Flo."""
from datetime import datetime, timedelta
import logging
from typing import Optional
from urllib.parse import urlparse

from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from .alarm import Alarm
from .device import Device
from .errors import RequestError
from .location import Location
from .presence import Presence
from .user import User
from .water import Water

_LOGGER = logging.getLogger(__name__)

API_V1_BASE: str = "https://api.meetflo.com/api/v1"
API_V2_BASE: str = "https://api-gw.meetflo.com/api/v2"

# Moen SSO (Cognito) auth. As of 2025, Flo accounts migrated to the Moen "Smart Water
# Network" identity now authenticate here, and api-gw rejects the legacy v1 token with
# 401. See ``use_sso``.
SSO_TOKEN_URL: str = (
    "https://4j1gkf0vji.execute-api.us-east-2.amazonaws.com/prod/v1/oauth2/token"
)
SSO_CLIENT_ID: str = "6qn9pep31dglq6ed4fvlq6rp5t"

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
            legacy Flo ``users/auth`` flow. Required for accounts that have migrated to
            the Moen Smart Water Network (the legacy token now gets a ``401`` from
            api-gw). Defaults to ``False`` for backwards compatibility.
        """
        self._password: str = password
        self._session: ClientSession = session
        self._token: Optional[str] = None
        self._token_expiration: Optional[datetime] = None
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

    async def _request(self, method: str, url: str, **kwargs) -> dict:
        """Make a request against the API."""
        if self._token_expiration and datetime.now() >= self._token_expiration:
            _LOGGER.info("Requesting new access token to replace expired one")

            # Nullify the token so that the authentication request doesn't use it:
            self._token = None

            # Nullify the expiration so the authentication request doesn't get caught
            # here:
            self._token_expiration = None

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

        if self._token:
            # The legacy token is used as-is; the SSO (Cognito) token is a bearer token.
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
                data: dict = await resp.json(content_type=None)
                resp.raise_for_status()
                return data
        except ClientError as err:
            raise RequestError(f"There was an error while requesting {url}") from err
        finally:
            if not use_running_session:
                await session.close()

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

    async def _async_authenticate_sso(self) -> None:
        """Authenticate via the Moen SSO (Cognito) flow.

        Exchanges username/password for a Cognito access token at the SSO token
        endpoint, then resolves the Flo user id from ``/users/me`` (the SSO token, unlike
        the legacy token, does not embed it).
        """
        auth_response: dict = await self._request(
            "post",
            SSO_TOKEN_URL,
            json={
                "username": self._username,
                "password": self._password,
                "client_id": SSO_CLIENT_ID,
            },
        )

        token: dict = auth_response["token"]
        self._token = token["access_token"]
        self._token_expiration = datetime.now() + timedelta(
            seconds=int(token.get("expires_in", 3600))
        )

        if not self._user_id:
            me: dict = await self._request("get", f"{API_V2_BASE}/users/me")
            self._user_id = me["id"]
            assert self._user_id
            self.user = User(self._request, self._user_id)


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
    :param use_sso: Use the Moen SSO (Cognito) auth flow; required for accounts migrated
        to the Moen Smart Water Network (the legacy token is rejected by api-gw with a
        ``401``). Defaults to ``False``.
    :type use_sso: ``bool``
    :rtype: :meth:`aioflo.api.API`
    """
    api = API(username, password, session=session, use_sso=use_sso)
    await api.async_authenticate()
    return api
