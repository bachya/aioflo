"""Define tests for user-related endpoints."""
import json

import aiohttp
import pytest

from aioflo import async_get_api

from .common import TEST_EMAIL_ADDRESS, TEST_PASSWORD, load_fixture


@pytest.mark.asyncio
async def test_get_user_info(aresponses, auth_success_response):
    """Test successfully retrieving user info."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/users/12345abcde",
        "get",
        aresponses.Response(
            text=load_fixture("user_info_base_response.json"), status=200
        ),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/users/12345abcde",
        "get",
        aresponses.Response(
            text=load_fixture("user_info_expand_alarm_settings_response.json"),
            status=200,
        ),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/users/12345abcde",
        "get",
        aresponses.Response(
            text=load_fixture("user_info_expand_locations_response.json"), status=200
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(session, TEST_EMAIL_ADDRESS, TEST_PASSWORD)
        user_info = await api.user.get_info()
        assert user_info["email"] == "email@address.com"
        assert not user_info["alarmSettings"]
        assert not user_info["locations"][0].get("devices")

        user_info = await api.user.get_info(include_alarm_settings=True)
        assert user_info["alarmSettings"]
        assert len(user_info["alarmSettings"][0]["settings"]) == 6

        user_info = await api.user.get_info(include_location_info=True)
        assert user_info["locations"][0]["devices"]
        assert user_info["locations"][0]["devices"][0]["id"] == "98765"
