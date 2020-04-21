"""Define tests for location-related endpoints."""
import json

import aiohttp
import pytest

from aioflo import async_get_api
from aioflo.errors import RequestError

from .common import TEST_EMAIL_ADDRESS, TEST_LOCATION_ID, TEST_PASSWORD, load_fixture


@pytest.mark.asyncio
async def test_get_location_info(aresponses, auth_success_response):
    """Test successfully retrieving location info."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/locations/mmnnoopp",
        "get",
        aresponses.Response(
            text=load_fixture("location_info_base_response.json"), status=200
        ),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/locations/mmnnoopp",
        "get",
        aresponses.Response(
            text=load_fixture("location_info_expand_devices_response.json"), status=200
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        location_info = await api.location.get_info(TEST_LOCATION_ID)
        assert location_info["address"] == "123 Main Street"
        assert len(location_info["devices"]) == 1
        assert not location_info["devices"][0].get("fwVersion")

        location_info = await api.location.get_info(
            TEST_LOCATION_ID, include_device_info=True
        )
        assert len(location_info["devices"]) == 1
        assert location_info["devices"][0]["fwVersion"]


@pytest.mark.asyncio
async def test_system_modes(aresponses, auth_success_response):
    """Test setting system modes.

    Since the API doesn't return responses after these actions, we merely test to ensure
    that no exceptions are thrown.
    """
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/locations/mmnnoopp/systemMode",
        "post",
        aresponses.Response(text=None, status=204),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/locations/mmnnoopp/systemMode",
        "post",
        aresponses.Response(text=None, status=204),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/locations/mmnnoopp/systemMode",
        "post",
        aresponses.Response(text=None, status=204),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)

        await api.location.set_mode_away(TEST_LOCATION_ID)
        await api.location.set_mode_home(TEST_LOCATION_ID)
        await api.location.set_mode_sleep(TEST_LOCATION_ID, 120)

        # No one should call this private method directly, but since a guard is in place
        # there, let's test it:
        with pytest.raises(RequestError):
            await api.location._set_system_mode(  # pylint: disable=protected-access
                TEST_LOCATION_ID, "fake_mode"
            )

        # Test various cases of using invalid parameter values in set_mode_sleep:
        with pytest.raises(RequestError):
            await api.location.set_mode_sleep(TEST_LOCATION_ID, 97)
        with pytest.raises(RequestError):
            await api.location.set_mode_sleep(
                TEST_LOCATION_ID, 120, revert_mode="sleep"
            )
