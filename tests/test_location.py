"""Define tests for location-related endpoints."""
# pylint: disable=protected-access,redefined-outer-name,unused-import
import json

import aiohttp
import pytest

from aioflo import async_get_api
from aioflo.errors import RequestError

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


@pytest.mark.asyncio
async def test_system_modes(aresponses, auth_success_json):
    """Test setting system modes.

    Since the API doesn't return responses after these actions, we merely test to ensure
    that no exceptions are thrown.
    """
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_json), status=200),
    )
    aresponses.add(
        "api.meetflo.com",
        "/api/v2/locations/mmnnoopp/systemMode",
        "post",
        aresponses.Response(text=None, status=204),
    )
    aresponses.add(
        "api.meetflo.com",
        "/api/v2/locations/mmnnoopp/systemMode",
        "post",
        aresponses.Response(text=None, status=204),
    )
    aresponses.add(
        "api.meetflo.com",
        "/api/v2/locations/mmnnoopp/systemMode",
        "post",
        aresponses.Response(text=None, status=204),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(session, TEST_EMAIL_ADDRESS, TEST_PASSWORD)

        await api.location.set_mode_away(TEST_LOCATION_ID)
        await api.location.set_mode_home(TEST_LOCATION_ID)
        await api.location.set_mode_sleep(TEST_LOCATION_ID, 120)

        # No one should call this private method directly, but since a guard is in place
        # there, let's test it:
        with pytest.raises(RequestError):
            await api.location._set_system_mode(TEST_LOCATION_ID, "fake_mode")

        # Test various cases of using invalid parameter values in set_mode_sleep:
        with pytest.raises(RequestError):
            await api.location.set_mode_sleep(TEST_LOCATION_ID, 97)
        with pytest.raises(RequestError):
            await api.location.set_mode_sleep(
                TEST_LOCATION_ID, 120, revert_mode="sleep"
            )
