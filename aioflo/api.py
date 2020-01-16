"""Define a base client for interacting with Flo."""
from datetime import datetime
from typing import Optional

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientError

from .errors import RequestError

API_V1_BASE: str = "https://api.meetflo.com/api/v1"

DEFAULT_HEADER_ACCEPT: str = "application/json, text/plain, */*"
DEFAULT_HEADER_CONTENT_TYPE: str = "application/json;charset=UTF-8"
DEFAULT_HEADER_HOST: str = "api.meetflo.com"
DEFAULT_HEADER_ORIGIN: str = "https://user.meetflo.com"
DEFAULT_HEADER_REFERER: str = "https://user.meetflo.com/login"
DEFAULT_HEADER_USER_AGENT: str = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36"
)


class API:  # pylint: disable=too-few-public-methods
    """Define the API object."""

    def __init__(self, session: ClientSession, username: str, password: str) -> None:
        """Initialize."""
        self._password: str = password
        self._session: ClientSession = session
        self._token: Optional[str] = None
        self._token_expiration: Optional[datetime] = None
        self._user_id: Optional[str] = None
        self._username: str = username

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
        if not headers:
            headers = {}
        headers.update(
            {
                "Accept": DEFAULT_HEADER_ACCEPT,
                "Content-Type": DEFAULT_HEADER_CONTENT_TYPE,
                "Host": DEFAULT_HEADER_HOST,
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
        """Authenticate the user and retrieve an authentication token."""
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
        self._user_id = auth_response["tokenPayload"]["user"]["user_id"]


async def async_get_api(session: ClientSession, username: str, password: str) -> API:
    """Instantiate an authenticated API object."""
    api = API(session, username, password)
    await api.async_authenticate()
    return api
