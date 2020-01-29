"""Define tests for alarm-related endpoints."""
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
        "/api/v2/alarms",
        "get",
        aresponses.Response(text=load_fixture("alarms_response.json"), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(session, TEST_EMAIL_ADDRESS, TEST_PASSWORD)
        alarm_info = await api.alarm.get_all()
        assert len(alarm_info["items"]) == 1
        assert alarm_info["items"][0]["name"] == "health_test_skipped"
