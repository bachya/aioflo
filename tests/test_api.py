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
    TEST_EMAIL_ADDRESS,
    TEST_PASSWORD,
    TEST_SSO_ACCESS_TOKEN,
    TEST_SSO_REFRESH_TOKEN,
    TEST_SSO_REFRESHED_TOKEN,
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


SSO_HOST = "4j1gkf0vji.execute-api.us-east-2.amazonaws.com"
SSO_PATH = "/prod/v1/oauth2/token"


@pytest.mark.asyncio
async def test_get_api_sso(aresponses, sso_auth_success_response, sso_users_me_response):
    """Test that the SSO flow authenticates and sends a bearer token."""
    aresponses.add(
        SSO_HOST,
        SSO_PATH,
        "post",
        aresponses.Response(text=json.dumps(sso_auth_success_response), status=200),
    )

    async def users_me_handler(request):
        """Assert the SSO token is sent as a bearer token."""
        assert request.headers["Authorization"] == f"Bearer {TEST_SSO_ACCESS_TOKEN}"
        return aresponses.Response(text=json.dumps(sso_users_me_response), status=200)

    aresponses.add("api-gw.meetflo.com", "/api/v2/users/me", "get", users_me_handler)

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(
            TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session, use_sso=True
        )
        assert api._token == TEST_SSO_ACCESS_TOKEN
        assert api._refresh_token == TEST_SSO_REFRESH_TOKEN
        assert api._user_id == TEST_USER_ID
        # Expiry is held back by SSO_EXPIRY_MARGIN so a request in flight cannot race
        # the real expiry, so it must land short of the full expires_in.
        # The upper bound must be well inside expires_in: `now` here is already later
        # than when the token was stored, so comparing against now+3600 would pass even
        # with no margin at all.
        assert api._token_expiration < datetime.now() + timedelta(seconds=3600 - 30)
        assert api._token_expiration > datetime.now() + timedelta(seconds=3600 - 120)


@pytest.mark.asyncio
async def test_sso_refresh_on_expiry(
    aresponses, sso_auth_success_response, sso_refresh_success_response,
    sso_users_me_response,
):
    """Test that an expired SSO token is replaced via the refresh grant."""
    aresponses.add(
        SSO_HOST,
        SSO_PATH,
        "post",
        aresponses.Response(text=json.dumps(sso_auth_success_response), status=200),
    )
    aresponses.add("api-gw.meetflo.com", "/api/v2/users/me", "get",
                   aresponses.Response(text=json.dumps(sso_users_me_response), status=200))

    async def refresh_handler(request):
        """Assert the refresh grant is used rather than username/password."""
        body = await request.json()
        assert body["grant_type"] == "refresh_token"
        assert body["refresh_token"] == TEST_SSO_REFRESH_TOKEN
        assert "password" not in body
        # The token endpoint must not be sent the (stale) access token:
        assert "Authorization" not in request.headers
        return aresponses.Response(
            text=json.dumps(sso_refresh_success_response), status=200
        )

    aresponses.add(SSO_HOST, SSO_PATH, "post", refresh_handler)
    aresponses.add("api-gw.meetflo.com", "/api/v2/ok", "get",
                   aresponses.Response(text=json.dumps({"ok": True}), status=200))

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(
            TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session, use_sso=True
        )
        api._token_expiration = datetime.now() - timedelta(seconds=1)
        await api._request("get", "https://api-gw.meetflo.com/api/v2/ok")

        assert api._token == TEST_SSO_REFRESHED_TOKEN
        # The refresh response omitted it, so the original must be retained:
        assert api._refresh_token == TEST_SSO_REFRESH_TOKEN


@pytest.mark.asyncio
async def test_sso_reauth_on_401(
    aresponses, sso_auth_success_response, sso_refresh_success_response,
    sso_users_me_response,
):
    """Test that a 401 mid-flight triggers a refresh and one retry."""
    aresponses.add(
        SSO_HOST,
        SSO_PATH,
        "post",
        aresponses.Response(text=json.dumps(sso_auth_success_response), status=200),
    )
    aresponses.add("api-gw.meetflo.com", "/api/v2/users/me", "get",
                   aresponses.Response(text=json.dumps(sso_users_me_response), status=200))
    # First call is rejected even though the token has not nominally expired:
    aresponses.add("api-gw.meetflo.com", "/api/v2/thing", "get",
                   aresponses.Response(text=None, status=401))

    async def refresh_after_401_handler(request):
        """The token endpoint must not receive the rejected access token.

        Unlike the expiry path, ``_token`` is still set when a 401 triggers this, so
        this is the case where suppressing the Authorization header actually matters.
        """
        assert "Authorization" not in request.headers
        return aresponses.Response(
            text=json.dumps(sso_refresh_success_response), status=200
        )

    aresponses.add(SSO_HOST, SSO_PATH, "post", refresh_after_401_handler)
    aresponses.add("api-gw.meetflo.com", "/api/v2/thing", "get",
                   aresponses.Response(text=json.dumps({"ok": True}), status=200))

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(
            TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session, use_sso=True
        )
        data = await api._request("get", "https://api-gw.meetflo.com/api/v2/thing")

        assert data == {"ok": True}
        assert api._token == TEST_SSO_REFRESHED_TOKEN
