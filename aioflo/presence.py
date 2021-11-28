"""Define /presence endpoints."""
from typing import Awaitable, Callable

from .const import API_V2_BASE


class Presence:  # pylint: disable=too-few-public-methods
    """Define an object to handle the endpoints."""

    def __init__(self, request: Callable[..., Awaitable]) -> None:
        """Initialize."""
        self._request: Callable[..., Awaitable] = request

    async def ping(self) -> dict:
        """Send a presence ping to Flo."""
        return await self._request("post", f"{API_V2_BASE}/presence/me")
