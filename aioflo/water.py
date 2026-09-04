"""Define /water endpoints."""

from collections.abc import Awaitable, Callable
from datetime import datetime

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
        location_id: str,
        start: datetime,
        end: datetime,
        interval: str = INTERVAL_HOURLY,
        device_mac_address: str | None = None,
    ) -> dict:
        """Return water consumption data.

        :param location_id: A Flo location UUID
        :type location_id: ``str``
        :param start: The start datetime of the range to examine
        :type start: ``datetime.datetime``
        :param end: The end datetime of the range to examine
        :type end: ``datetime.datetime``
        :param interval: Aggregation interval (``1h``, ``1d``, or ``1m``)
        :type interval: ``str``
        :param device_mac_address: Limit results to a single device at the location
        :type device_mac_address: ``Optional[str]``
        :rtype: ``dict``
        """
        raise_on_invalid_argument(interval, INTERVALS)

        params = {
            "endDate": end.isoformat(),
            "interval": interval,
            "locationId": location_id,
            "startDate": start.isoformat(),
        }
        if device_mac_address:
            params["macAddress"] = device_mac_address.replace(":", "")

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
        """Return water usage metrics for a device.

        :param device_mac_address: MAC address of the Flo device
        :type device_mac_address: ``str``
        :param start: The start datetime of the range to examine
        :type start: ``datetime.datetime``
        :param end: The end datetime of the range to examine
        :type end: ``datetime.datetime``
        :param interval: Aggregation interval (``1h``, ``1d``, or ``1m``)
        :type interval: ``str``
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
