"""Define /water endpoints."""
from datetime import datetime
from typing import Awaitable, Callable

from .const import API_V2_BASE
from .util import raise_on_invalid_argument

INTERVAL_DAILY = "1d"
INTERVAL_HOURLY = "1h"
INTERVAL_MONTHLY = "1m"
INTERVALS = set([INTERVAL_DAILY, INTERVAL_HOURLY, INTERVAL_MONTHLY])


class Water:  # pylint: disable=too-few-public-methods
    """Define an object to handle the endpoints."""

    def __init__(self, request: Callable[..., Awaitable]) -> None:
        """Initialize."""
        self._request: Callable[..., Awaitable] = request

    async def get_consumption_info(
        self,
        location_id: str,
        start: datetime,
        end: datetime,
        interval: str = INTERVAL_HOURLY,
    ) -> dict:
        """Return user account data.

        :param location_id: A Flo location UUID
        :type location_id: ``str``
        :param start: The start datetime of the range to examine
        :type start: ``datetime.datetime``
        :param end: The end datetime of the range to examine
        :type end: ``datetime.datetime``
        :rtype: ``dict``
        """
        raise_on_invalid_argument(interval, INTERVALS)

        return await self._request(
            "get",
            f"{API_V2_BASE}/water/consumption",
            params={
                "endDate": end.isoformat(),
                "interval": interval,
                "locationId": location_id,
                "startDate": start.isoformat(),
            },
        )

    async def get_metrics(
        self,
        device_mac_address: str,
        start: datetime,
        end: datetime,
        interval: str = INTERVAL_HOURLY,
    ) -> dict:
        """Return user account data.

        :param start: The start datetime of the range to examine
        :type start: ``datetime.datetime``
        :param end: The end datetime of the range to examine
        :type end: ``datetime.datetime``
        :rtype: ``dict``
        """
        raise_on_invalid_argument(interval, INTERVALS)

        return await self._request(
            "get",
            f"{API_V2_BASE}/water/metrics",
            params={
                "endDate": end.isoformat(),
                "interval": interval,
                "macAddress": device_mac_address.replace(":", ""),
                "startDate": start.isoformat(),
            },
        )
