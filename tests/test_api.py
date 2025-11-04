"""Define general tests for the API."""
# pylint: disable=protected-access
from datetime import datetime, timedelta
import json
import logging

import aiohttp
import pytest

from aioflo import async_get_api
from aioflo.errors import RequestError

from .common import (
    TEST_ACCESS_TOKEN,
    TEST_EMAIL_ADDRESS,
    TEST_PASSWORD,
    TEST_REFRESH_TOKEN,
    TEST_TOKEN,
    TEST_USER_ID,
)


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
        assert any("Access token expired, attempting to refresh" in e.message for e in caplog.records)


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


@pytest.mark.asyncio
async def test_oauth2_authentication(aresponses, oauth2_success_response):
    """Test OAuth2 authentication flow."""
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v1/oauth2/token",
        "post",
        aresponses.Response(text=json.dumps(oauth2_success_response), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        assert api._token == TEST_ACCESS_TOKEN
        assert api._refresh_token == TEST_REFRESH_TOKEN
        assert api._user_id == TEST_USER_ID
        assert api._use_oauth2 is True


@pytest.mark.asyncio
async def test_oauth2_token_refresh(
    aresponses, oauth2_success_response, oauth2_refresh_response, caplog
):
    """Test that OAuth2 token refresh works when access token expires."""
    caplog.set_level(logging.INFO)

    # Initial OAuth2 authentication
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v1/oauth2/token",
        "post",
        aresponses.Response(text=json.dumps(oauth2_success_response), status=200),
    )
    # Token refresh request
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v1/oauth2/token",
        "post",
        aresponses.Response(text=json.dumps(oauth2_refresh_response), status=200),
    )
    # Actual API request after refresh
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/random_good_endpoint",
        "get",
        aresponses.Response(text=json.dumps({}), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)

        # Verify initial OAuth2 authentication
        assert api._token == TEST_ACCESS_TOKEN
        assert api._refresh_token == TEST_REFRESH_TOKEN

        # Expire the token to trigger refresh
        api._token_expiration = datetime.now() - timedelta(days=1)

        # Make a request that should trigger token refresh
        await api._request("get", "https://api.meetflo.com/api/v1/random_good_endpoint")

        # Verify token was refreshed
        assert api._token == f"{TEST_ACCESS_TOKEN}_refreshed"
        assert api._refresh_token == f"{TEST_REFRESH_TOKEN}_refreshed"
        assert any("Refreshing access token" in e.message for e in caplog.records)


@pytest.mark.asyncio
async def test_oauth2_fallback_to_legacy(aresponses, auth_success_response, caplog):
    """Test that authentication falls back to legacy when OAuth2 fails."""
    caplog.set_level(logging.INFO)

    # OAuth2 authentication fails
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v1/oauth2/token",
        "post",
        aresponses.Response(text=json.dumps({"error": "invalid_grant"}), status=401),
    )
    # Legacy authentication succeeds
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)

        # Verify fallback to legacy authentication
        assert api._token == TEST_TOKEN
        assert api._user_id == TEST_USER_ID
        assert api._refresh_token is None
        assert api._use_oauth2 is False
        assert any("OAuth2 authentication failed" in e.message for e in caplog.records)
        assert any("Using legacy authentication" in e.message for e in caplog.records)
