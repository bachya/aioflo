"""Define tests for user-related endpoints."""
import json

import aiohttp
import pytest

from aioflo import async_get_api

from .common import TEST_EMAIL_ADDRESS, TEST_PASSWORD, load_fixture


@pytest.mark.asyncio
async def test_ping(aresponses, auth_success_response):
    """Test successfully retrieving user info."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/presence/me",
        "post",
        aresponses.Response(text=load_fixture("ping_response.json"), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        ping_response = await api.presence.ping()
        assert ping_response["ipAddress"] == "11.111.111.111"
        assert ping_response["userId"] == "12345abcde"
        assert ping_response["action"] == "report"
        assert ping_response["type"] == "user"
        assert ping_response["appName"] == "legacy"
        assert ping_response["userData"]["account"]["type"] == "personal"
