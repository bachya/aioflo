"""Define general test fixtures."""
import time

import pytest

from ..const import TEST_EMAIL_ADDRESS, TEST_TOKEN, TEST_USER_ID


@pytest.fixture()
def auth_success_json():
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
