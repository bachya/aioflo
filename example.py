"""Run an example script to quickly test."""
import asyncio
import logging

from aiohttp import ClientSession

from aioflo import async_get_api
from aioflo.errors import FloError

_LOGGER = logging.getLogger()

EMAIL = "<EMAIL>"
PASSWORD = "<PASSWORD>"


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
        except FloError as err:
            _LOGGER.error("There was an error: %s", err)


asyncio.get_event_loop().run_until_complete(main())
