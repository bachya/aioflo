"""Define a base client for interacting with Flo."""
from datetime import datetime
import logging
from typing import Optional
from urllib.parse import urlparse

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientError

from .alarm import Alarm
from .errors import RequestError
from .location import Location
from .user import User
from .water import Water

_LOGGER = logging.getLogger(__name__)

API_V1_BASE: str = "https://api.meetflo.com/api/v1"

DEFAULT_HEADER_ACCEPT: str = "application/json, text/plain, */*"
DEFAULT_HEADER_CONTENT_TYPE: str = "application/json;charset=UTF-8"
DEFAULT_HEADER_ORIGIN: str = "https://user.meetflo.com"
DEFAULT_HEADER_REFERER: str = "https://user.meetflo.com/home"
DEFAULT_HEADER_USER_AGENT: str = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36"
)


class API:  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Define the API object."""

    def __init__(self, session: ClientSession, username: str, password: str) -> None:
        """Initialize."""
        self._password: str = password
        self._session: ClientSession = session
        self._token: Optional[str] = None
        self._token_expiration: Optional[datetime] = None
        self._user_id: Optional[str] = None
        self._username: str = username

        self.alarm: Alarm = Alarm(self._request)
        self.location: Location = Location(self._request)
        self.water: Water = Water(self._request)

        # These endpoints will get instantiated post-authentication:
        self.user: Optional[User] = None

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict = None,
        params: dict = None,
        json: dict = None,
    ) -> dict:
        """Make a request against the API."""
        if self._token_expiration and datetime.now() >= self._token_expiration:
            _LOGGER.info("Requesting new access token to replace expired one")

            # Nullify the token so that the authentication request doesn't use it:
            self._token = None

            # Nullify the expiration so the authentication request doesn't get caught
            # here:
            self._token_expiration = None

            await self.async_authenticate()

        if not headers:
            headers = {}
        headers.update(
            {
                "Accept": DEFAULT_HEADER_ACCEPT,
                "Content-Type": DEFAULT_HEADER_CONTENT_TYPE,
                "Host": urlparse(url).netloc,
                "Origin": DEFAULT_HEADER_ORIGIN,
                "Referer": DEFAULT_HEADER_REFERER,
                "User-Agent": DEFAULT_HEADER_USER_AGENT,
            }
        )

        if self._token:
            headers["Authorization"] = self._token

        async with self._session.request(
            method, url, headers=headers, params=params, json=json
        ) as resp:
            data: dict = await resp.json(content_type=None)
            try:
                resp.raise_for_status()
                return data
            except ClientError as err:
                raise RequestError(f"There was an error while requesting {url}: {err}")

    async def async_authenticate(self) -> None:
        """Authenticate the user and set the access token with its expiration."""
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
            self.user = User(self._request, self._user_id)


async def async_get_api(session: ClientSession, username: str, password: str) -> API:
    """Instantiate an authenticated API object.

    :param session: An ``aiohttp`` ``ClientSession``
    :type session: ``aiohttp.client.ClientSession``
    :param email: A Flo email address
    :type email: ``str``
    :param password: A Flo password
    :type password: ``str``
    :rtype: :meth:`aioflo.api.API`
    """
    api = API(session, username, password)
    await api.async_authenticate()
    return api
