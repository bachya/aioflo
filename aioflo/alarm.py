"""Define /alarms endpoints."""
from typing import Awaitable, Callable

from .const import API_V2_BASE


class Alarm:  # pylint: disable=too-few-public-methods
    """Define an object to handle the endpoints."""

    def __init__(self, request: Callable[..., Awaitable]) -> None:
        """Initialize."""
        self._request: Callable[..., Awaitable] = request

    async def get_all(self, lang: str = "en"):
        """Get all alarms.

        :param lang: Language code for alarm messages (default: "en")
        :type lang: ``str``
        :rtype: ``dict``
        """
        params = {"lang": lang}
        return await self._request("get", f"{API_V2_BASE}/alarms", params=params)
