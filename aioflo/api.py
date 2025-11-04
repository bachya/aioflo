"""Define a base client for interacting with Flo."""
from datetime import datetime, timedelta
import logging
from typing import Optional
from urllib.parse import urlparse

from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError

from .alarm import Alarm
from .const import (
    API_V1_BASE,
    OAUTH2_CLIENT_ID,
    OAUTH2_CLIENT_SECRET,
    OAUTH2_GRANT_TYPE_PASSWORD,
    OAUTH2_GRANT_TYPE_REFRESH,
    OAUTH2_TOKEN_ENDPOINT,
)
from .device import Device
from .errors import RequestError
from .location import Location
from .presence import Presence
from .user import User
from .water import Water

_LOGGER = logging.getLogger(__name__)

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
        client_id: str = OAUTH2_CLIENT_ID,
        client_secret: str = OAUTH2_CLIENT_SECRET,
    ) -> None:
        """Initialize.

        Args:
            username: Flo account username/email
            password: Flo account password
            session: Optional aiohttp ClientSession for connection pooling
            client_id: OAuth2 client ID (uses default shared app credentials)
            client_secret: OAuth2 client secret (uses default shared app credentials)
        """
        self._client_id: str = client_id
        self._client_secret: str = client_secret
        self._password: str = password
        self._session: ClientSession = session
        self._token: Optional[str] = None
        self._token_expiration: Optional[datetime] = None
        self._refresh_token: Optional[str] = None
        self._user_id: Optional[str] = None
        self._username: str = username
        self._use_oauth2: bool = True  # Try OAuth2 first, fallback to old auth

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
            _LOGGER.info("Access token expired, attempting to refresh")

            # Try to refresh using refresh_token if available (OAuth2)
            if self._refresh_token:
                try:
                    await self._async_refresh_token()
                except RequestError:
                    _LOGGER.warning(
                        "Refresh token failed, re-authenticating with credentials"
                    )
                    # Nullify tokens and re-authenticate
                    self._token = None
                    self._token_expiration = None
                    self._refresh_token = None
                    await self.async_authenticate()
            else:
                # No refresh token, re-authenticate with credentials
                self._token = None
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
            # OAuth2 tokens use "Bearer" prefix, legacy tokens don't
            if self._use_oauth2 and self._refresh_token:
                kwargs["headers"]["Authorization"] = f"Bearer {self._token}"
            else:
                kwargs["headers"]["Authorization"] = self._token

        use_running_session = self._session and not self._session.closed

        if use_running_session:
            session = self._session
        else:
            session = ClientSession(timeout=ClientTimeout(total=DEFAULT_TIMEOUT))

        try:
            async with session.request(method, url, **kwargs) as resp:
                resp.raise_for_status()
                data: dict = await resp.json(content_type=None)
                return data
        except ClientError as err:
            raise RequestError(f"There was an error while requesting {url}") from err
        finally:
            if not use_running_session:
                await session.close()

    async def _async_oauth2_authenticate(self) -> None:
        """Authenticate using OAuth2 password grant flow."""
        auth_response: dict = await self._request(
            "post",
            OAUTH2_TOKEN_ENDPOINT,
            json={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": OAUTH2_GRANT_TYPE_PASSWORD,
                "username": self._username,
                "password": self._password,
            },
        )

        self._token = auth_response["access_token"]
        self._refresh_token = auth_response["refresh_token"]

        # Parse expiration from ISO format or use expires_in
        if "expires_at" in auth_response:
            # Parse timezone-aware datetime and convert to naive local time
            expires_at = datetime.fromisoformat(
                auth_response["expires_at"].replace("Z", "+00:00")
            )
            # Convert to naive datetime for consistency with legacy auth
            self._token_expiration = expires_at.replace(tzinfo=None)
        else:
            # Fallback: use expires_in seconds
            self._token_expiration = datetime.now() + timedelta(
                seconds=auth_response["expires_in"]
            )

        if not self._user_id:
            self._user_id = auth_response["user_id"]
            assert self._user_id
            self.user = User(self._request, self._user_id)

    async def _async_refresh_token(self) -> None:
        """Refresh the access token using the refresh token."""
        if not self._refresh_token:
            raise RequestError("No refresh token available")

        _LOGGER.info("Refreshing access token using refresh token")

        # Temporarily clear expiration to prevent infinite recursion during refresh
        self._token_expiration = None

        auth_response: dict = await self._request(
            "post",
            OAUTH2_TOKEN_ENDPOINT,
            json={
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "grant_type": OAUTH2_GRANT_TYPE_REFRESH,
                "refresh_token": self._refresh_token,
            },
        )

        self._token = auth_response["access_token"]
        self._refresh_token = auth_response["refresh_token"]

        # Parse expiration from ISO format or use expires_in
        if "expires_at" in auth_response:
            # Parse timezone-aware datetime and convert to naive local time
            expires_at = datetime.fromisoformat(
                auth_response["expires_at"].replace("Z", "+00:00")
            )
            # Convert to naive datetime for consistency with legacy auth
            self._token_expiration = expires_at.replace(tzinfo=None)
        else:
            # Fallback: use expires_in seconds
            self._token_expiration = datetime.now() + timedelta(
                seconds=auth_response["expires_in"]
            )

    async def _async_legacy_authenticate(self) -> None:
        """Authenticate using the legacy username/password flow."""
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

    async def async_authenticate(self) -> None:
        """Authenticate the user and set the access token with its expiration.

        Tries OAuth2 authentication first, falls back to legacy auth if that fails.
        """
        if self._use_oauth2:
            try:
                _LOGGER.info("Attempting OAuth2 authentication")
                await self._async_oauth2_authenticate()
                _LOGGER.info("OAuth2 authentication successful")
                return
            except (RequestError, KeyError, ValueError) as err:
                _LOGGER.warning(
                    "OAuth2 authentication failed (%s), falling back to legacy auth",
                    err,
                )
                # Disable OAuth2 for future attempts in this session
                self._use_oauth2 = False

        # Use legacy authentication
        _LOGGER.info("Using legacy authentication")
        await self._async_legacy_authenticate()


async def async_get_api(
    username: str, password: str, *, session: Optional[ClientSession] = None
) -> API:
    """Instantiate an authenticated API object.

    :param session: An ``aiohttp`` ``ClientSession``
    :type session: ``aiohttp.client.ClientSession``
    :param email: A Flo email address
    :type email: ``str``
    :param password: A Flo password
    :type password: ``str``
    :rtype: :meth:`aioflo.api.API`
    """
    api = API(username, password, session=session)
    await api.async_authenticate()
    return api
