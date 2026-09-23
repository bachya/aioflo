"""Define package constants."""

API_V2_BASE: str = "https://api-gw.meetflo.com/api/v2"

# Shutoff valves without a water-temperature sensor do not omit tempF from
# telemetry; they report a fixed placeholder (225 on the units this was written
# against). No domestic supply reaches boiling, so a reading at or above this is
# a sentinel rather than a measurement.
IMPLAUSIBLE_WATER_TEMP_F: float = 212.0
