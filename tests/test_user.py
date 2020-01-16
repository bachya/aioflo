"""Define tests for user-related endpoints."""
# pylint: disable=protected-access,redefined-outer-name,unused-import
import json

import aiohttp
import pytest

from aioflo import async_get_api

from .const import (
    RESPONSE_USER_INFO_BASE,
    RESPONSE_USER_INFO_EXPAND_ALARM_SETTINGS,
    TEST_EMAIL_ADDRESS,
    TEST_PASSWORD,
)
from .fixtures import auth_success_json  # noqa


@pytest.mark.asyncio
async def test_get_user_info(aresponses, auth_success_json):
    """Test successfully retrieving user info."""
    user_info_with_alarm_settings = {
        **RESPONSE_USER_INFO_BASE,
        **RESPONSE_USER_INFO_EXPAND_ALARM_SETTINGS,
    }

    user_info_with_locations = {
        **RESPONSE_USER_INFO_BASE,
        **RESPONSE_USER_INFO_EXPAND_ALARM_SETTINGS,
    }

    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_json), status=200),
    )
    aresponses.add(
        "api.meetflo.com",
        "/api/v2/users/12345abcde",
        "get",
        aresponses.Response(text=json.dumps(RESPONSE_USER_INFO_BASE), status=200),
    )
    aresponses.add(
        "api.meetflo.com",
        "/api/v2/users/12345abcde",
        "get",
        aresponses.Response(text=json.dumps(user_info_with_alarm_settings), status=200),
    )
    aresponses.add(
        "api.meetflo.com",
        "/api/v2/users/12345abcde",
        "get",
        aresponses.Response(text=json.dumps(user_info_with_locations), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(session, TEST_EMAIL_ADDRESS, TEST_PASSWORD)
        user_info = await api.user.get_info()
        assert user_info == RESPONSE_USER_INFO_BASE

        user_info = await api.user.get_info(include_alarm_settings=True)
        assert user_info == user_info_with_alarm_settings

        user_info = await api.user.get_info(include_location_info=True)
        assert user_info == user_info_with_locations
