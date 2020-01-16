"""Run an example script to quickly test."""
import asyncio
import logging

from aiohttp import ClientSession

from aioflo import async_get_client
from aioflo.errors import NotionError

_LOGGER = logging.getLogger()

EMAIL = "email@address.com"
PASSWORD = "password"


async def main() -> None:
    """Create the aiohttp session and run the example."""
    logging.basicConfig(level=logging.INFO)
    async with ClientSession() as session:
        try:
            client = await async_get_client(EMAIL, PASSWORD, session)

            bridges = await client.bridge.async_all()
            _LOGGER.info("BRIDGES: %s", bridges)

            sensors = await client.sensor.async_all()
            _LOGGER.info("SENSORS: %s", sensors)

            systems = await client.system.async_all()
            _LOGGER.info("SYSTEMS: %s", systems)

            tasks = await client.task.async_all()
            _LOGGER.info("TASKS: %s", tasks)
        except NotionError as err:
            _LOGGER.error("There was an error: %s", err)


asyncio.get_event_loop().run_until_complete(main())
