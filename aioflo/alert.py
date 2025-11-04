"""Define /alerts endpoints."""
from typing import Awaitable, Callable, List

from .const import API_V2_BASE


class Alert:  # pylint: disable=too-few-public-methods
    """Define an object to handle the endpoints."""

    def __init__(self, request: Callable[..., Awaitable]) -> None:
        """Initialize."""
        self._request: Callable[..., Awaitable] = request

    async def get_all(
        self, device_ids: List[str], page: int = 1, size: int = 100
    ) -> dict:
        """Get all alerts for specified devices.

        :param device_ids: List of device IDs to get alerts for
        :type device_ids: ``List[str]``
        :param page: Page number for pagination (default: 1)
        :type page: ``int``
        :param size: Number of results per page (default: 100)
        :type size: ``int``
        :rtype: ``dict``
        """
        params = {"page": page, "size": size}

        # Add multiple deviceId parameters (same key repeated)
        # aiohttp will handle this correctly
        for device_id in device_ids:
            if "deviceId" not in params:
                params["deviceId"] = []
            if not isinstance(params["deviceId"], list):
                params["deviceId"] = [params["deviceId"]]
            params["deviceId"].append(device_id)

        return await self._request("get", f"{API_V2_BASE}/alerts", params=params)
