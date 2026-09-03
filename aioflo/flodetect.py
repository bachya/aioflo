"""Define /flodetect endpoints."""
from datetime import datetime
from typing import Awaitable, Callable, Optional

from .const import API_V2_BASE


class Flodetect:  # pylint: disable=too-few-public-methods
    """Define an object to handle the endpoints."""

    def __init__(self, request: Callable[..., Awaitable]) -> None:
        """Initialize."""
        self._request: Callable[..., Awaitable] = request

    async def get_events(
        self,
        device_mac_address: str,
        *,
        to: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> dict:
        """Return Flo Detect water-flow events for a device.

        :param device_mac_address: MAC address of the Flo device
        :type device_mac_address: ``str``
        :param to: Return events at or before this datetime
        :type to: ``Optional[datetime.datetime]``
        :param limit: Maximum number of events to return
        :type limit: ``Optional[int]``
        :rtype: ``dict``
        """
        params = {"macAddress": device_mac_address.replace(":", "")}
        if to is not None:
            params["to"] = to.isoformat()
        if limit is not None:
            params["limit"] = str(limit)

        return await self._request(
            "get",
            f"{API_V2_BASE}/flodetect/events",
            params=params,
        )
