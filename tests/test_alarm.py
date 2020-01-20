"""Define tests for alarm-related endpoints."""
# pylint: disable=protected-access,redefined-outer-name,unused-import
import json

import aiohttp
import pytest

from aioflo import async_get_api

from .const import RESPONSE_ALARMS, TEST_EMAIL_ADDRESS, TEST_PASSWORD
from .fixtures import auth_success_json  # noqa


@pytest.mark.asyncio
async def test_get_user_info(aresponses, auth_success_json):
    """Test successfully retrieving user info."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_json), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/alarms",
        "get",
        aresponses.Response(text=json.dumps(RESPONSE_ALARMS), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(session, TEST_EMAIL_ADDRESS, TEST_PASSWORD)
        alarm_info = await api.alarm.get_all()
        assert alarm_info == RESPONSE_ALARMS
