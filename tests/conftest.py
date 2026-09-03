"""Define fixtures available for all tests."""
import time

import pytest

from .common import (
    TEST_EMAIL_ADDRESS,
    TEST_SSO_ACCESS_TOKEN,
    TEST_SSO_REFRESH_TOKEN,
    TEST_SSO_REFRESHED_TOKEN,
    TEST_TOKEN,
    TEST_USER_ID,
)


@pytest.fixture()
def auth_success_response():
    """Define a response to /api/v1/users/auth."""
    now = round(time.time())

    return {
        "token": TEST_TOKEN,
        "tokenPayload": {
            "user": {"user_id": TEST_USER_ID, "email": TEST_EMAIL_ADDRESS},
            "timestamp": now,
        },
        "tokenExpiration": 86400,
        "timeNow": now,
    }


@pytest.fixture()
def sso_auth_success_response():
    """Define a response to the Moen SSO oauth2/token endpoint."""
    return {
        "token": {
            "access_token": TEST_SSO_ACCESS_TOKEN,
            "refresh_token": TEST_SSO_REFRESH_TOKEN,
            "token_type": "Bearer",
            "expires_in": 3600,
        }
    }


@pytest.fixture()
def sso_refresh_success_response():
    """Define a refresh-grant response, which omits the refresh token."""
    return {
        "token": {
            "access_token": TEST_SSO_REFRESHED_TOKEN,
            "token_type": "Bearer",
            "expires_in": 3600,
        }
    }


@pytest.fixture()
def sso_users_me_response():
    """Define a response to /api/v2/users/me."""
    return {"id": TEST_USER_ID, "email": TEST_EMAIL_ADDRESS}
