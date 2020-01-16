"""Define /location endpoints."""
from typing import Awaitable, Callable, Optional

from .const import API_V2_BASE
from .errors import RequestError

SYSTEM_MODE_AWAY = "away"
SYSTEM_MODE_HOME = "home"
SYSTEM_MODE_SLEEP = "sleep"
SYSTEM_MODES = set([SYSTEM_MODE_AWAY, SYSTEM_MODE_HOME, SYSTEM_MODE_SLEEP])
SYSTEM_REVERT_MODES = set([SYSTEM_MODE_AWAY, SYSTEM_MODE_HOME])

# The Flo web app hardcodes sleep durations to certain intervals; testing seems to
# indicate that those are the only valid values, so we stick with them:
SLEEP_MINUTE_OPTIONS = set([120, 1440, 4320])


class Location:
    """Define an object to handle the endpoints."""

    def __init__(self, request: Callable[..., Awaitable]) -> None:
        """Initialize."""
        self._request: Callable[..., Awaitable] = request

    async def _set_system_mode(
        self, location_id: str, mode: str, additional_payload: Optional[dict] = None
    ) -> None:
        """Set the system mode (with optional parameters)."""
        if mode not in SYSTEM_MODES:
            raise RequestError(f"Cannot set invalid system mode: {mode}")

        payload = {"target": "mode"}
        if additional_payload:
            payload = {**payload, **additional_payload}
        await self._request(
            "post", f"{API_V2_BASE}/locations/{location_id}/systemMode", json=payload
        )

    async def get_info(
        self, location_id: str, include_device_info: bool = False,
    ) -> dict:
        """Return user account data.

        :param include_device_info: Include expanded device information
        :type include_device_info: ``bool``
        :rtype: ``dict``
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

    async def set_mode_away(self, location_id: str) -> None:
        """Set the system mode to "Away".

        :param location_id: A Flo location UUID
        :type location_id: ``str``
        """
        await self._set_system_mode(location_id, SYSTEM_MODE_AWAY)

    async def set_mode_home(self, location_id: str) -> None:
        """Set the system mode to "Home".

        :param location_id: A Flo location UUID
        :type location_id: ``str``
        """
        await self._set_system_mode(location_id, SYSTEM_MODE_HOME)

    async def set_mode_sleep(
        self,
        location_id: str,
        revert_minutes: int,
        revert_mode: Optional[str] = SYSTEM_MODE_HOME,
    ) -> None:
        """Set the system mode to "Home".

        :param location_id: A Flo location UUID
        :type location_id: ``str``
        :param revert_minutes: The number of minutes to sleep (120, 1440, or 4320)
        :type revert_minutes: ``int``
        :param revert_mode: The mode to set after sleep concludes ("away" or "home")
        :type revert_mode: ``str``
        """
        if revert_minutes not in SLEEP_MINUTE_OPTIONS:
            raise RequestError(
                (
                    f"Cannot set invalid revert duration: {revert_minutes} "
                    "(valid options: {SLEEP_MINUTE_OPTIONS})"
                )
            )

        if revert_mode not in SYSTEM_REVERT_MODES:
            raise RequestError(
                (
                    f"Cannot set invalid revert mode: {revert_mode} "
                    "(valid options: {SYSTEM_REVERT_MODES})"
                )
            )

        await self._set_system_mode(
            location_id,
            SYSTEM_MODE_HOME,
            additional_payload={
                "revertMinutes": revert_minutes,
                "revert_mode": revert_mode,
            },
        )
