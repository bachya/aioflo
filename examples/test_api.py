"""Run an example script to quickly test."""
import asyncio
from datetime import datetime
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
            api = await async_get_api(EMAIL, PASSWORD, session=session)

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

            first_device_id = location_info["devices"][0]["id"]
            device_info = await api.device.get_info(first_device_id)
            _LOGGER.info(device_info)

            health_test_response = await api.device.run_health_test(first_device_id)
            _LOGGER.info(health_test_response)

            close_valve_response = await api.device.close_valve(first_device_id)
            _LOGGER.info(close_valve_response)

            open_valve_response = await api.device.open_valve(first_device_id)
            _LOGGER.info(open_valve_response)

        except FloError as err:
            _LOGGER.error("There was an error: %s", err)


asyncio.run(main())
