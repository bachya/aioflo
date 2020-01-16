"""Define /location endpoints."""
from typing import Awaitable, Callable

from .const import API_V2_BASE


class Location:  # pylint: disable=too-few-public-methods
    """Define an object to handle the endpoints."""

    def __init__(self, request: Callable[..., Awaitable]) -> None:
        """Initialize."""
        self._request: Callable[..., Awaitable] = request

    async def get_info(
        self, location_id: str, include_device_info: bool = False,
    ) -> dict:
        """Return user account data.

        :param include_device_info: Include expanded device information
        :type label: bool
        :rtype: dict
        """
        additional_info = []
        if include_device_info:
            additional_info.append("devices")

        params = {}
        if additional_info:
            params["expand"] = ",".join(additional_info)

        return await self._request(
            "get", f"{API_V2_BASE}/locations/{location_id}", params=params
        )
