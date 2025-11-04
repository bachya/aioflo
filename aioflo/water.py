"""Define /water endpoints."""
from datetime import datetime
from typing import Awaitable, Callable

from .const import API_V2_BASE
from .util import raise_on_invalid_argument

INTERVAL_DAILY = "1d"
INTERVAL_HOURLY = "1h"
INTERVAL_MONTHLY = "1m"
INTERVALS = {INTERVAL_DAILY, INTERVAL_HOURLY, INTERVAL_MONTHLY}


class Water:  # pylint: disable=too-few-public-methods
    """Define an object to handle the endpoints."""

    def __init__(self, request: Callable[..., Awaitable]) -> None:
        """Initialize."""
        self._request: Callable[..., Awaitable] = request

    async def get_consumption_info(
        self,
        location_id: str = None,
        start: datetime = None,
        end: datetime = None,
        interval: str = INTERVAL_HOURLY,
        mac_address: str = None,
    ) -> dict:
        """Return water consumption data.

        :param location_id: A Flo location UUID (use either this or mac_address)
        :type location_id: ``str``
        :param start: The start datetime of the range to examine
        :type start: ``datetime.datetime``
        :param end: The end datetime of the range to examine
        :type end: ``datetime.datetime``
        :param interval: Time interval for data aggregation (1h, 1d, 1m)
        :type interval: ``str``
        :param mac_address: Device MAC address (use either this or location_id)
        :type mac_address: ``str``
        :rtype: ``dict``
        """
        raise_on_invalid_argument(interval, INTERVALS)

        params = {
            "interval": interval,
        }

        # Add date parameters if provided
        if start:
            params["startDate"] = start.isoformat()
        if end:
            params["endDate"] = end.isoformat()

        # Use either locationId or macAddress
        if location_id:
            params["locationId"] = location_id
        elif mac_address:
            params["macAddress"] = mac_address.replace(":", "")

        return await self._request(
            "get",
            f"{API_V2_BASE}/water/consumption",
            params=params,
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
