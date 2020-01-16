"""Define /water endpoints."""
from datetime import datetime
from typing import Awaitable, Callable

from .const import API_V2_BASE
from .errors import RequestError

CONSUMPTION_INTERVAL_DAILY = "1d"
CONSUMPTION_INTERVAL_HOURLY = "1h"
CONSUMPTION_INTERVAL_MONTHLY = "1m"
CONSUMPTION_INTERVALS = set(
    [
        CONSUMPTION_INTERVAL_DAILY,
        CONSUMPTION_INTERVAL_HOURLY,
        CONSUMPTION_INTERVAL_MONTHLY,
    ]
)


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
        interval: str = CONSUMPTION_INTERVAL_HOURLY,
    ) -> dict:
        """Return user account data.

        :param start: The start datetime of the range to examine
        :type start: ``datetime.datetime``
        :param end: The end datetime of the range to examine
        :type end: ``datetime.datetime``
        :rtype: ``dict``
        """
        if interval not in CONSUMPTION_INTERVALS:
            raise RequestError(
                (
                    f"Cannot use invalid duration: {interval} "
                    "(valid options: {CONSUMPTION_INTERVALS})"
                )
            )

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
