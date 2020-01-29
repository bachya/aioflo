"""Define tests for water-related endpoints."""
from datetime import datetime
import json

import aiohttp
import pytest

from aioflo import async_get_api
from aioflo.errors import RequestError

from .common import (
    TEST_EMAIL_ADDRESS,
    TEST_LOCATION_ID,
    TEST_MAC_ADDRESS,
    TEST_PASSWORD,
    load_fixture,
)


@pytest.mark.asyncio
async def test_get_consumption_info(aresponses, auth_success_response):
    """Test successfully retrieving location info."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/water/consumption",
        "get",
        aresponses.Response(
            text=load_fixture("water_consumption_info_response.json"), status=200
        ),
    )

    start = datetime(2020, 1, 16, 0, 0)
    end = datetime(2020, 1, 16, 23, 59, 59, 999000)

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(session, TEST_EMAIL_ADDRESS, TEST_PASSWORD)
        consumption_info = await api.water.get_consumption_info(
            TEST_LOCATION_ID, start, end
        )
        assert len(consumption_info["items"]) == 5

        # Test various cases of using invalid parameter values in set_mode_sleep:
        with pytest.raises(RequestError):
            await api.water.get_consumption_info(
                TEST_LOCATION_ID, start, end, interval="a_totally_fake_interval",
            )


@pytest.mark.asyncio
async def test_get_metrics(aresponses, auth_success_response):
    """Test successfully retrieving location info."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/water/metrics",
        "get",
        aresponses.Response(
            text=load_fixture("water_metric_info_response.json"), status=200
        ),
    )

    start = datetime(2020, 1, 16, 0, 0)
    end = datetime(2020, 1, 16, 23, 59, 59, 999000)

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(session, TEST_EMAIL_ADDRESS, TEST_PASSWORD)
        metrics = await api.water.get_metrics(TEST_MAC_ADDRESS, start, end)
        assert len(metrics["items"]) == 3

        # Test various cases of using invalid parameter values in set_mode_sleep:
        with pytest.raises(RequestError):
            await api.water.get_metrics(
                TEST_MAC_ADDRESS, start, end, interval="a_totally_fake_interval",
            )
