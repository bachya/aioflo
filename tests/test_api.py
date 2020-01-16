"""Define general tests for the API."""
# pylint: disable=protected-access,redefined-outer-name,unused-import
import json

import aiohttp
import pytest

from aioflo import async_get_api
from aioflo.errors import RequestError

from .const import TEST_EMAIL_ADDRESS, TEST_PASSWORD, TEST_TOKEN, TEST_USER_ID
from .fixtures import auth_success_json  # noqa


@pytest.mark.asyncio
async def test_bad_api_call(aresponses, auth_success_json):
    """Test that an HTTP error raises the correct error."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_json), status=200),
    )
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/bad",
        "get",
        aresponses.Response(text=None, status=404),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(session, TEST_EMAIL_ADDRESS, TEST_PASSWORD)
        with pytest.raises(RequestError):
            await api._request("get", "https://api.meetflo.com/api/v1/bad")


@pytest.mark.asyncio
async def test_get_api(aresponses, auth_success_json):
    """Test instantiating an authenticated API object."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_json), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(session, TEST_EMAIL_ADDRESS, TEST_PASSWORD)
        assert api._token == TEST_TOKEN
        assert api._user_id == TEST_USER_ID
