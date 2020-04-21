"""Define general tests for the API."""
# pylint: disable=protected-access
from datetime import datetime, timedelta
import json
import logging

import aiohttp
import pytest

from aioflo import async_get_api
from aioflo.errors import RequestError

from .common import TEST_EMAIL_ADDRESS, TEST_PASSWORD, TEST_TOKEN, TEST_USER_ID


@pytest.mark.asyncio
async def test_bad_api_call(aresponses, auth_success_response):
    """Test that an HTTP error raises the correct error."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/bad",
        "get",
        aresponses.Response(text=None, status=404),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        with pytest.raises(RequestError):
            await api._request("get", "https://api.meetflo.com/api/v1/bad")


@pytest.mark.asyncio
async def test_expired_api_token(aresponses, auth_success_response, caplog):
    """Test that auto-renewal of the access token works."""
    caplog.set_level(logging.INFO)

    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/random_good_endpoint",
        "get",
        aresponses.Response(text=None, status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        print(api._token_expiration)
        api._token_expiration = datetime.now() - timedelta(days=1)
        print(api._token_expiration)
        await api._request("get", "https://api.meetflo.com/api/v1/random_good_endpoint")
        assert any("Requesting new access token" in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_get_api(aresponses, auth_success_response):
    """Test instantiating an authenticated API object."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        assert api._token == TEST_TOKEN
        assert api._user_id == TEST_USER_ID
