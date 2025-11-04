"""Example demonstrating OAuth2 authentication with aioflo.

This example shows how to use OAuth2 authentication with the Flo API.
OAuth2 is the recommended authentication method and includes:
- Automatic token refresh when tokens expire
- More secure than legacy authentication
- Better handling of token lifecycle

The library uses shared application credentials extracted from the
Moen Flo mobile app, so you only need to provide your email and password.
"""
import asyncio
from datetime import datetime
import logging

from aiohttp import ClientSession

from aioflo import async_get_api
from aioflo.errors import FloError

_LOGGER = logging.getLogger(__name__)

EMAIL = "<EMAIL>"
PASSWORD = "<PASSWORD>"


async def main() -> None:
    """Create the aiohttp session and run the example."""
    logging.basicConfig(level=logging.INFO)

    async with ClientSession() as session:
        try:
            # Get an authenticated API instance
            # OAuth2 authentication is attempted first, with automatic fallback
            # to legacy authentication if OAuth2 is unavailable
            _LOGGER.info("Authenticating with Flo API...")
            api = await async_get_api(EMAIL, PASSWORD, session=session)
            _LOGGER.info("Authentication successful!")

            # The API object automatically handles token refresh
            # You don't need to manually refresh tokens - it happens automatically
            # when making requests after the token expires

            # Get user account information
            _LOGGER.info("Fetching user information...")
            user_info = await api.user.get_info()
            _LOGGER.info("User: %s", user_info.get("user", {}).get("email"))

            # Get the first location
            if not user_info.get("locations"):
                _LOGGER.warning("No locations found for this account")
                return

            first_location_id = user_info["locations"][0]["id"]
            _LOGGER.info("First location ID: %s", first_location_id)

            # Get location information with device details
            _LOGGER.info("Fetching location information...")
            location_info = await api.location.get_info(
                first_location_id,
                include_device_info=True
            )
            _LOGGER.info("Location: %s", location_info.get("name", "Unknown"))

            # Get device information
            if not location_info.get("devices"):
                _LOGGER.warning("No devices found at this location")
                return

            first_device_id = location_info["devices"][0]["id"]
            _LOGGER.info("First device ID: %s", first_device_id)

            device_info = await api.device.get_info(first_device_id)
            _LOGGER.info("Device: %s (Battery: %s%%)",
                        device_info.get("nickname", "Unknown"),
                        device_info.get("batteryLevel", {}).get("percent", "N/A"))

            # Get water consumption data for today
            _LOGGER.info("Fetching water consumption data...")
            today = datetime.now()
            start_time = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = today.replace(hour=23, minute=59, second=59, microsecond=999000)

            consumption_info = await api.water.get_consumption_info(
                first_location_id,
                start_time,
                end_time,
            )
            _LOGGER.info("Water consumption data retrieved for %s",
                        today.strftime("%Y-%m-%d"))

            # Get alerts for the location
            _LOGGER.info("Fetching alerts...")
            alerts = await api.alert.get_alerts(first_location_id)
            _LOGGER.info("Found %d alerts", len(alerts))

            # Example: Set location mode (commented out to avoid changing settings)
            # await api.location.set_mode_home(first_location_id)
            # _LOGGER.info("Location mode set to 'Home'")

            # Example: Run a health test (commented out to avoid triggering actual test)
            # health_test_response = await api.device.run_health_test(first_device_id)
            # _LOGGER.info("Health test initiated: %s", health_test_response)

            # Ping the presence endpoint
            ping_response = await api.presence.ping()
            _LOGGER.info("Presence ping successful: %s", ping_response)

            _LOGGER.info("All operations completed successfully!")

        except FloError as err:
            _LOGGER.error("Error communicating with Flo API: %s", err)
        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err)


if __name__ == "__main__":
    asyncio.run(main())
