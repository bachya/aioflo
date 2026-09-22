"""Define /device endpoints."""

from collections.abc import Awaitable, Callable

from .const import API_V2_BASE, IMPLAUSIBLE_WATER_TEMP_F


class Device:  # pylint: disable=too-few-public-methods
    """Define an object to handle the endpoints."""

    def __init__(self, request: Callable[..., Awaitable]) -> None:
        """Initialize."""
        self._request: Callable[..., Awaitable] = request

    async def get_info(self, device_id: str) -> dict:
        """Return device specific data.

        `telemetry.current.tempF` is normalized to ``None`` when the device
        reports the no-sensor placeholder; see :func:`_normalize_telemetry`.

        :param device_id: Unique identifier for the device
        :type device_id: ``str``
        :rtype: ``dict``
        """
        device_info = await self._request("get", f"{API_V2_BASE}/devices/{device_id}")
        _normalize_telemetry(device_info)
        return device_info

    async def run_health_test(self, device_id: str) -> dict:
        """Run a health test for a specific device.

        :param device_id: Unique identifier for the device
        :type device_id: ``str``
        :rtype: ``dict``
        """
        return await self._request(
            "post", f"{API_V2_BASE}/devices/{device_id}/healthTest/run"
        )

    async def open_valve(self, device_id: str) -> dict:
        """Open the valve for a specific device.

        `telemetry.current.tempF` is normalized to ``None`` when the device
        reports the no-sensor placeholder; see :func:`_normalize_telemetry`.

        :param device_id: Unique identifier for the device
        :type device_id: ``str``
        :rtype: ``dict``
        """
        device_info = await self._request(
            "post",
            f"{API_V2_BASE}/devices/{device_id}",
            json={"valve": {"target": "open"}},
        )
        _normalize_telemetry(device_info)
        return device_info

    async def close_valve(self, device_id: str) -> dict:
        """Close the valve for a specific device.

        `telemetry.current.tempF` is normalized to ``None`` when the device
        reports the no-sensor placeholder; see :func:`_normalize_telemetry`.

        :param device_id: Unique identifier for the device
        :type device_id: ``str``
        :rtype: ``dict``
        """
        device_info = await self._request(
            "post",
            f"{API_V2_BASE}/devices/{device_id}",
            json={"valve": {"target": "closed"}},
        )
        _normalize_telemetry(device_info)
        return device_info


def _clear_implausible_temp(values: dict, key: str) -> None:
    """Replace a no-sensor placeholder in ``values[key]`` with ``None``.

    ``key`` is ``tempF`` on a device's current telemetry and ``averageTempF``
    on a metrics bucket. The cutoff is boiling; see ``_normalize_telemetry``.
    """
    temperature = values.get(key)
    if (
        isinstance(temperature, (int, float))
        and temperature >= IMPLAUSIBLE_WATER_TEMP_F
    ):
        values[key] = None


def _normalize_telemetry(device_info: dict) -> None:
    """Replace the no-sensor water-temperature placeholder with ``None``.

    A shutoff valve with no water-temperature sensor does not omit ``tempF``,
    it returns a constant placeholder (225 on the units this was written
    against). Passed through, that is indistinguishable from a measurement:
    consumers chart it, store it, and trigger on it.

    The check is against boiling rather than the specific value observed, so it
    does not depend on every unit using the same sentinel. Detectors report
    ambient air temperature through the same field and cannot approach it.
    """
    current = (device_info.get("telemetry") or {}).get("current")
    if not isinstance(current, dict):
        return
    _clear_implausible_temp(current, "tempF")
