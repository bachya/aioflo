"""Define tests for location-related endpoints."""
# pylint: disable=protected-access,redefined-outer-name,unused-import
import json

import aiohttp
import pytest

from aioflo import async_get_api

from .const import (
    RESPONSE_LOCATION_INFO_BASE,
    RESPONSE_LOCATION_INFO_EXPAND_LOCATIONS,
    TEST_EMAIL_ADDRESS,
    TEST_LOCATION_ID,
    TEST_PASSWORD,
)
from .fixtures import auth_success_json  # noqa


@pytest.mark.asyncio
async def test_get_location_info(aresponses, auth_success_json):
    """Test successfully retrieving location info."""
    location_info_with_devices = {
        **RESPONSE_LOCATION_INFO_BASE,
        **RESPONSE_LOCATION_INFO_EXPAND_LOCATIONS,
    }

    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_json), status=200),
    )
    aresponses.add(
        "api.meetflo.com",
        "/api/v2/locations/mmnnoopp",
        "get",
        aresponses.Response(text=json.dumps(RESPONSE_LOCATION_INFO_BASE), status=200),
    )
    aresponses.add(
        "api.meetflo.com",
        "/api/v2/locations/mmnnoopp",
        "get",
        aresponses.Response(text=json.dumps(location_info_with_devices), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(session, TEST_EMAIL_ADDRESS, TEST_PASSWORD)
        location_info = await api.location.get_info(TEST_LOCATION_ID)
        assert location_info == RESPONSE_LOCATION_INFO_BASE

        location_info = await api.location.get_info(
            TEST_LOCATION_ID, include_device_info=True
        )
        assert location_info == location_info_with_devices
