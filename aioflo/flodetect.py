"""Define /flodetect endpoints."""

from collections.abc import Awaitable, Callable
from datetime import datetime

from .const import API_V2_BASE


class Flodetect:  # pylint: disable=too-few-public-methods
    """Define an object to handle the endpoints."""

    def __init__(self, request: Callable[..., Awaitable]) -> None:
        """Initialize."""
        self._request: Callable[..., Awaitable] = request

    @staticmethod
    def parse_events(payload: dict) -> list[dict]:
        """Flatten a /flodetect/events payload into a list of event dicts.

        The live API groups events per device::

            {"params": {...}, "items": [{"macAddress": "...", "events": [...]}]}

        Each event uses ``startAt``, ``endAt``, ``totalGal``, ``duration``, and
        ``predicted.displayText`` (not a flat ``items`` list of events).
        """
        events: list[dict] = []
        for item in payload.get("items") or []:
            events.extend(item.get("events") or [])
        return events

    async def get_events(
        self,
        device_mac_address: str,
        *,
        to: datetime | None = None,
        limit: int | None = None,
    ) -> dict:
        """Return Flo Detect water-flow events for a device.

        The raw payload groups events per device under ``items[].events``.
        Pass it to :meth:`parse_events` to get a flat list.

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
