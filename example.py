"""Run an example script to quickly test."""
import asyncio
from datetime import datetime
import logging

from aiohttp import ClientSession

from aioflo import async_get_api
from aioflo.errors import FloError

_LOGGER = logging.getLogger()

EMAIL = "jwilhelmy@gmail.com"
PASSWORD = "Jo3rulez"


async def main() -> None:
    """Create the aiohttp session and run the example."""
    logging.basicConfig(level=logging.INFO)
    async with ClientSession() as session:
        try:
            api = await async_get_api(session, EMAIL, PASSWORD)

            user_info = await api.user.get_info()
            _LOGGER.info(user_info)

            first_location_id = user_info["locations"][0]["id"]
            location_info = await api.location.get_info(first_location_id)
            _LOGGER.info(location_info)

            consumption_info = await api.water.get_consumption_info(
                first_location_id,
                datetime(2020, 1, 16, 0, 0),
                datetime(2020, 1, 16, 23, 59, 59, 999000),
            )
            _LOGGER.info(consumption_info)
        except FloError as err:
            _LOGGER.error("There was an error: %s", err)


asyncio.get_event_loop().run_until_complete(main())
