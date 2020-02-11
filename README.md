# 💧 aioflo: a Python3, asyncio-friendly library for Notion® Home Monitoring

[![CI](https://github.com/bachya/aioflo/workflows/CI/badge.svg)](https://github.com/bachya/aioflo/actions)
[![PyPi](https://img.shields.io/pypi/v/aioflo.svg)](https://pypi.python.org/pypi/aioflo)
[![Version](https://img.shields.io/pypi/pyversions/aioflo.svg)](https://pypi.python.org/pypi/aioflo)
[![License](https://img.shields.io/pypi/l/aioflo.svg)](https://github.com/bachya/aioflo/blob/master/LICENSE)
[![Code Coverage](https://codecov.io/gh/bachya/aioflo/branch/master/graph/badge.svg)](https://codecov.io/gh/bachya/aioflo)
[![Maintainability](https://api.codeclimate.com/v1/badges/1b6949e0c97708925315/maintainability)](https://codeclimate.com/github/bachya/aioflo/maintainability)
[![Say Thanks](https://img.shields.io/badge/SayThanks-!-1EAEDB.svg)](https://saythanks.io/to/bachya)

`aioflo` is a Python 3, `asyncio`-friendly library for interacting with
[Flo by Moen Smart Water Detectors](https://www.moen.com/flo).

# Python Versions

`aioflo` is currently supported on:

* Python 3.6
* Python 3.7
* Python 3.8

# Installation

```python
pip install aioflo
```

# Usage

`aioflo` starts within an
[aiohttp](https://aiohttp.readthedocs.io/en/stable/) `ClientSession`:

```python
import asyncio

from aiohttp import ClientSession

from aioflo import Client


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as websession:
        # YOUR CODE HERE


asyncio.get_event_loop().run_until_complete(main())
```

Create an API object, initialize it, then get to it:

```python
import asyncio

from aiohttp import ClientSession

from aioflo import async_get_api


async def main() -> None:
    """Create the aiohttp session and run the example."""
    async with ClientSession() as websession:
        api = await async_get_api(session, "<EMAIL>", "<PASSWORD>")

        # Get user account information:
        user_info = await api.user.get_info()
        a_location_id = user_info["locations"][0]["id"]

        # Get location (i.e., device) information:
        location_info = await api.location.get_info(a_location_id)

        # Get consumption info between a start and end datetime:
        consumption_info = await api.water.get_consumption_info(
            a_location_id,
            datetime(2020, 1, 16, 0, 0),
            datetime(2020, 1, 16, 23, 59, 59, 999000),
        )

        # Get various other metrics related to water usage:
        metrics = await api.water.get_metrics(
            "<DEVICE_MAC_ADDRESS>",
            datetime(2020, 1, 16, 0, 0),
            datetime(2020, 1, 16, 23, 59, 59, 999000),
        )

        # Set the device in "Away" mode:
        await set_mode_away(a_location_id)

        # Set the device in "Home" mode:
        await set_mode_home(a_location_id)

        # Set the device in "Sleep" mode for 120 minutes, then return to "Away" mode:
        await set_mode_sleep(a_location_id, 120, "away")

asyncio.get_event_loop().run_until_complete(main())
```

See the module docstrings throughout the library for full info on all parameters, return
types, etc.

# Contributing

1. [Check for open features/bugs](https://github.com/bachya/aioflo/issues)
  or [initiate a discussion on one](https://github.com/bachya/aioflo/issues/new).
2. [Fork the repository](https://github.com/bachya/aioflo/fork).
3. (_optional, but highly recommended_) Create a virtual environment: `python3 -m venv .venv`
4. (_optional, but highly recommended_) Enter the virtual environment: `source ./venv/bin/activate`
5. Install the dev environment: `script/setup`
6. Code your new feature or bug fix.
7. Write tests that cover your new functionality.
8. Run tests and ensure 100% code coverage: `script/test`
9. Update `README.md` with any new documentation.
10. Add yourself to `AUTHORS.md`.
11. Submit a pull request!
