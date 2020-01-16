"""Define /user endpoints."""
from typing import Awaitable, Callable

from .const import API_V2_BASE


class User:  # pylint: disable=too-few-public-methods
    """Define an object to handle the endpoints."""

    def __init__(self, request: Callable[..., Awaitable], user_id: str) -> None:
        """Initialize."""
        self._request: Callable[..., Awaitable] = request
        self._user_id: str = user_id

    async def get_info(
        self, include_alarm_settings: bool = False, include_location_info: bool = False
    ) -> dict:
        """Return user account data.

        :param include_alarm_settings: Include expanded alarm information
        :type include_alarm_settings: ``bool``
        :param include_location_info: Include expanded location info
        :type include_location_info: ``bool``
        :rtype: ``dict``
        """
        additional_info = []
        if include_alarm_settings:
            additional_info.append("alarmSettings")
        if include_location_info:
            additional_info.append("locations")

        params = {}
        if additional_info:
            params["expand"] = ",".join(additional_info)

        return await self._request(
            "get", f"{API_V2_BASE}/users/{self._user_id}", params=params
        )
