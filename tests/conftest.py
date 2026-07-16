"""Define fixtures available for all tests."""
import time

import pytest

from .common import TEST_EMAIL_ADDRESS, TEST_TOKEN, TEST_USER_ID


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
            "id_token": "id-token",
            "access_token": TEST_TOKEN,
            "token_type": "Bearer",
            "refresh_token": "refresh-token",
            "expires_in": 3600,
        }
    }


@pytest.fixture()
def sso_users_me_response():
    """Define a response to /api/v2/users/me (resolves the user id in SSO mode)."""
    return {"id": TEST_USER_ID, "email": TEST_EMAIL_ADDRESS}
