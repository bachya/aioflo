"""Define /device endpoints."""
from typing import Awaitable, Callable

from .const import API_V2_BASE


class Device:  # pylint: disable=too-few-public-methods
    """Define an object to handle the endpoints."""

    def __init__(self, request: Callable[..., Awaitable]) -> None:
        """Initialize."""
        self._request: Callable[..., Awaitable] = request

    async def get_info(self, device_id: str) -> dict:
        """Return device specific data.

        :param device_id: Unique identifier for the device
        :type device_id: ``str``
        :rtype: ``dict``
        """
        return await self._request("get", f"{API_V2_BASE}/devices/{device_id}")

    async def run_health_test(self, device_id: str) -> None:
        """Run a health test for a specific device.

        :param device_id: Unique identifier for the device
        :type device_id: ``str``
        :rtype: ``dict``
        """
        return await self._request(
            "post", f"{API_V2_BASE}/devices/{device_id}/healthTest/run"
        )

    async def open_valve(self, device_id: str) -> None:
        """Open the valve for a specific device.

        :param device_id: Unique identifier for the device
        :type device_id: ``str``
        :rtype: ``dict``
        """
        return await self._request(
            "post",
            f"{API_V2_BASE}/devices/{device_id}",
            json={"valve": {"target": "open"}},
        )

    async def close_valve(self, device_id: str) -> None:
        """Close the valve for a specific device.

        :param device_id: Unique identifier for the device
        :type device_id: ``str``
        :rtype: ``dict``
        """
        return await self._request(
            "post",
            f"{API_V2_BASE}/devices/{device_id}",
            json={"valve": {"target": "closed"}},
        )
