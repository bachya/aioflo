# 💧 aioflo: a Python3, asyncio-friendly library for Flo Smart Water Detectors

[![CI](https://github.com/bachya/aioflo/workflows/CI/badge.svg)](https://github.com/bachya/aioflo/actions)
[![PyPi](https://img.shields.io/pypi/v/aioflo.svg)](https://pypi.python.org/pypi/aioflo)
[![Version](https://img.shields.io/pypi/pyversions/aioflo.svg)](https://pypi.python.org/pypi/aioflo)
[![License](https://img.shields.io/pypi/l/aioflo.svg)](https://github.com/bachya/aioflo/blob/main/LICENSE)
[![Code Coverage](https://codecov.io/gh/bachya/aioflo/branch/dev/graph/badge.svg)](https://codecov.io/gh/bachya/aioflo)
[![Maintainability](https://api.codeclimate.com/v1/badges/1b6949e0c97708925315/maintainability)](https://codeclimate.com/github/bachya/aioflo/maintainability)
[![Say Thanks](https://img.shields.io/badge/SayThanks-!-1EAEDB.svg)](https://saythanks.io/to/bachya)

<a href="https://www.buymeacoffee.com/bachya1208P" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

`aioflo` is a Python 3, `asyncio`-friendly library for interacting with
[Flo by Moen Smart Water Detectors](https://www.moen.com/flo).

# Python Versions

`aioflo` is currently supported on:

* Python 3.9
* Python 3.10
* Python 3.11
* Python 3.12
* Python 3.13
* Python 3.14

# Installation

```bash
pip install aioflo
```

# Usage

```python
import asyncio
from datetime import datetime

from aioflo import async_get_api


async def main() -> None:
    """Run!"""
    api = await async_get_api("<EMAIL>", "<PASSWORD>")

    # Get user account information:
    user_info = await api.user.get_info()
    a_location_id = user_info["locations"][0]["id"]

    # Get location (i.e., device) information:
    location_info = await api.location.get_info(a_location_id)

    # Get device information
    first_device = location_info["devices"][0]
    first_device_id = first_device["id"]
    device_info = await api.device.get_info(first_device_id)

    # Get all alarms:
    alarms = await api.alarm.get_all()

    # Run a health test
    health_test_response = await api.device.run_health_test(first_device_id)

    # Close the shutoff valve
    close_valve_response = await api.device.close_valve(first_device_id)

    # Open the shutoff valve
    open_valve_response = await api.device.open_valve(first_device_id)

    # Get consumption info between a start and end datetime (location-wide aggregate):
    consumption_info = await api.water.get_consumption_info(
        a_location_id,
        datetime(2020, 1, 16, 0, 0),
        datetime(2020, 1, 16, 23, 59, 59, 999000),
    )

    # Scope consumption to a single device. Pass device_mac_address when a location
    # has multiple Flo devices; omit it for the location-wide total:
    device_consumption = await api.water.get_consumption_info(
        a_location_id,
        datetime(2020, 1, 16, 0, 0),
        datetime(2020, 1, 16, 23, 59, 59, 999000),
        device_mac_address=first_device["macAddress"],
    )

    # Get various other metrics related to water usage:
    metrics = await api.water.get_metrics(
        first_device["macAddress"],
        datetime(2020, 1, 16, 0, 0),
        datetime(2020, 1, 16, 23, 59, 59, 999000),
    )

    # Get recent Flo Detect water-flow events (near-real-time usage):
    events = await api.flodetect.get_events(
        first_device["macAddress"],
        to=datetime(2026, 7, 12, 10, 25, 4),
        limit=20,
    )

    # Set the device in "Away" mode:
    await api.location.set_mode_away(a_location_id)

    # Set the device in "Home" mode:
    await api.location.set_mode_home(a_location_id)

    # Set the device in "Sleep" mode for 120 minutes, then return to "Away" mode:
    await api.location.set_mode_sleep(a_location_id, 120, "away")


asyncio.run(main())
```

By default, the library creates a new connection to Flo with each coroutine. If you are
calling a large number of coroutines (or merely want to squeeze out every second of
runtime savings possible), an
[`aiohttp`](https://github.com/aio-libs/aiohttp) `ClientSession` can be used for connection
pooling:

```python
import asyncio
from datetime import datetime

from aiohttp import ClientSession

from aioflo import async_get_api


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as session:
        api = await async_get_api("<EMAIL>", "<PASSWORD>", session=session)

        # Tell Flo to get updated data from the device
        ping_response = await api.presence.ping()

        # Get user account information:
        user_info = await api.user.get_info()
        a_location_id = user_info["locations"][0]["id"]

        # Get location (i.e., device) information:
        location_info = await api.location.get_info(a_location_id)

        # Get device information
        first_device = location_info["devices"][0]
        first_device_id = first_device["id"]
        device_info = await api.device.get_info(first_device_id)

        # Get all alarms:
        alarms = await api.alarm.get_all()

        # Run a health test
        health_test_response = await api.device.run_health_test(first_device_id)

        # Close the shutoff valve
        close_valve_response = await api.device.close_valve(first_device_id)

        # Open the shutoff valve
        open_valve_response = await api.device.open_valve(first_device_id)

        # Get consumption info between a start and end datetime (location-wide aggregate):
        consumption_info = await api.water.get_consumption_info(
            a_location_id,
            datetime(2020, 1, 16, 0, 0),
            datetime(2020, 1, 16, 23, 59, 59, 999000),
        )

        # Scope consumption to a single device. Pass device_mac_address when a location
        # has multiple Flo devices; omit it for the location-wide total:
        device_consumption = await api.water.get_consumption_info(
            a_location_id,
            datetime(2020, 1, 16, 0, 0),
            datetime(2020, 1, 16, 23, 59, 59, 999000),
            device_mac_address=first_device["macAddress"],
        )

        # Get various other metrics related to water usage:
        metrics = await api.water.get_metrics(
            first_device["macAddress"],
            datetime(2020, 1, 16, 0, 0),
            datetime(2020, 1, 16, 23, 59, 59, 999000),
        )

        # Get recent Flo Detect water-flow events (near-real-time usage):
        events = await api.flodetect.get_events(
            first_device["macAddress"],
            to=datetime(2026, 7, 12, 10, 25, 4),
            limit=20,
        )

        # Set the device in "Away" mode:
        await api.location.set_mode_away(a_location_id)

        # Set the device in "Home" mode:
        await api.location.set_mode_home(a_location_id)

        # Set the device in "Sleep" mode for 120 minutes, then return to "Away" mode:
        await api.location.set_mode_sleep(a_location_id, 120, "away")


asyncio.run(main())
```

## Moen SSO (Cognito) auth

The current Moen Smartwater app authenticates against Moen's SSO endpoint rather than the
legacy Flo `users/auth` flow. `use_sso=True` opts into it: the access token is sent to
`api-gw.meetflo.com` as a bearer token and is refreshed on expiry and on a `401`, falling
back to a full login if the refresh token is rejected.

```python
api = await async_get_api("<EMAIL>", "<PASSWORD>", use_sso=True)
```

The legacy flow is the default and is unchanged. The legacy endpoint still works, so this
is cover for it being retired rather than a fix for a current failure.
