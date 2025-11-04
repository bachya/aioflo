"""Define fixtures available for all tests."""
from datetime import datetime, timedelta
import time

import pytest

from .common import (
    TEST_ACCESS_TOKEN,
    TEST_EMAIL_ADDRESS,
    TEST_REFRESH_TOKEN,
    TEST_TOKEN,
    TEST_USER_ID,
)


@pytest.fixture()
def auth_success_response():
    """Define a response to /api/v1/users/auth (legacy auth)."""
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
def oauth2_success_response():
    """Define a response to /api/v1/oauth2/token (OAuth2 auth)."""
    expires_at = datetime.now() + timedelta(days=1)

    return {
        "access_token": TEST_ACCESS_TOKEN,
        "refresh_token": TEST_REFRESH_TOKEN,
        "expires_in": 86400,
        "user_id": TEST_USER_ID,
        "expires_at": expires_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z",
        "issued_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z",
        "token_type": "Bearer",
    }


@pytest.fixture()
def oauth2_refresh_response():
    """Define a response to /api/v1/oauth2/token (refresh token grant)."""
    expires_at = datetime.now() + timedelta(days=1)

    return {
        "access_token": f"{TEST_ACCESS_TOKEN}_refreshed",
        "refresh_token": f"{TEST_REFRESH_TOKEN}_refreshed",
        "expires_in": 86400,
        "expires_at": expires_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z",
        "issued_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-4] + "Z",
        "token_type": "Bearer",
    }
