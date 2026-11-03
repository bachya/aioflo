"""Define tests for water-related endpoints."""

from datetime import datetime, timedelta, timezone
import json
from unittest.mock import AsyncMock

import aiohttp
import pytest

from aioflo import async_get_api
from aioflo.errors import RequestError
from aioflo.water import Water

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
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        consumption_info = await api.water.get_consumption_info(
            TEST_LOCATION_ID, start, end
        )
        assert len(consumption_info["items"]) == 5

        consumption_info = await api.water.get_consumption_info(
            TEST_LOCATION_ID, start, end, device_mac_address=TEST_MAC_ADDRESS
        )
        assert len(consumption_info["items"]) == 5

        # Test various cases of using invalid parameter values in set_mode_sleep:
        with pytest.raises(RequestError):
            await api.water.get_consumption_info(
                TEST_LOCATION_ID,
                start,
                end,
                interval="a_totally_fake_interval",
            )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "timezone_kwargs",
    [{}, {"timezone": None}, {"timezone": "America/Denver"}, {"timezone": ""}],
)
@pytest.mark.parametrize("mac", [None, TEST_MAC_ADDRESS])
@pytest.mark.parametrize("tzinfo", [None, timezone(timedelta(hours=-7))])
async def test_consumption_query(
    aresponses, auth_success_response, timezone_kwargs, mac, tzinfo
):
    """Preserve serialized dates and device filtering when forwarding timezone."""
    start = datetime(2020, 1, 16, tzinfo=tzinfo)
    end = datetime(2020, 1, 16, 23, 59, 59, 999000, tzinfo=tzinfo)
    expected = {
        "locationId": TEST_LOCATION_ID,
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "interval": "1d",
    }
    if mac is not None:
        expected["macAddress"] = mac.replace(":", "")
    if timezone_kwargs.get("timezone") is not None:
        expected["tz"] = timezone_kwargs["timezone"]
    queries = []

    async def consumption_handler(request):
        queries.append(dict(request.query))
        return aresponses.Response(
            text=load_fixture("water_consumption_info_response.json"), status=200
        )

    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com", "/api/v2/water/consumption", "get", consumption_handler
    )
    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        result = await api.water.get_consumption_info(
            TEST_LOCATION_ID, start, end, "1d", mac, **timezone_kwargs
        )

    assert queries == [expected]
    assert result == json.loads(load_fixture("water_consumption_info_response.json"))
    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
@pytest.mark.parametrize("timezone_kwargs", [{}, {"timezone": "America/Denver"}])
async def test_consumption_defaults_and_request_errors(
    aresponses, auth_success_response, timezone_kwargs
):
    """Keep hourly defaults and propagate HTTP failures with or without timezone."""
    queries = []

    async def consumption_handler(request):
        queries.append(dict(request.query))
        return aresponses.Response(status=500)

    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com", "/api/v2/water/consumption", "get", consumption_handler
    )
    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        with pytest.raises(RequestError):
            await api.water.get_consumption_info(
                TEST_LOCATION_ID,
                datetime(2020, 1, 16),
                datetime(2020, 1, 17),
                **timezone_kwargs,
            )

    expected = {
        "locationId": TEST_LOCATION_ID,
        "startDate": "2020-01-16T00:00:00",
        "endDate": "2020-01-17T00:00:00",
        "interval": "1h",
    }
    if timezone_kwargs:
        expected["tz"] = timezone_kwargs["timezone"]
    assert queries == [expected]
    aresponses.assert_plan_strictly_followed()


@pytest.mark.asyncio
async def test_consumption_invalid_arguments():
    """Reject invalid intervals and positional timezone before making a request."""
    request = AsyncMock()
    water = Water(request)
    start = datetime(2020, 1, 16)
    end = datetime(2020, 1, 17)
    with pytest.raises(RequestError):
        await water.get_consumption_info(
            TEST_LOCATION_ID, start, end, "invalid", timezone="America/Denver"
        )
    with pytest.raises(TypeError):
        await water.get_consumption_info(
            TEST_LOCATION_ID, start, end, "1h", TEST_MAC_ADDRESS, "America/Denver"
        )
    request.assert_not_called()


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
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        metrics = await api.water.get_metrics(TEST_MAC_ADDRESS, start, end)
        assert len(metrics["items"]) == 3

        # Test various cases of using invalid parameter values in set_mode_sleep:
        with pytest.raises(RequestError):
            await api.water.get_metrics(
                TEST_MAC_ADDRESS,
                start,
                end,
                interval="a_totally_fake_interval",
            )


@pytest.mark.asyncio
async def test_get_metrics_normalizes_temperature_placeholder(
    aresponses, auth_success_response
):
    """Metrics buckets use the same no-sensor placeholder as live telemetry."""
    metrics_payload = json.loads(load_fixture("water_metric_info_response.json"))
    metrics_payload["items"][0]["averageTempF"] = 225
    metrics_payload["items"][1]["averageTempF"] = 212
    metrics_payload["items"][2]["averageTempF"] = None
    metrics_payload["items"].append(
        {
            "time": "2020-01-16T03:00:00-07:00",
            "averageGpm": None,
            "averagePsi": 77.0,
            "averageTempF": 211.9,
        }
    )
    pressures = [item["averagePsi"] for item in metrics_payload["items"]]

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
        aresponses.Response(text=json.dumps(metrics_payload), status=200),
    )

    start = datetime(2020, 1, 16, 0, 0)
    end = datetime(2020, 1, 16, 23, 59, 59, 999000)

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        metrics = await api.water.get_metrics(TEST_MAC_ADDRESS, start, end)
        temperatures = [item["averageTempF"] for item in metrics["items"]]
        assert temperatures == [None, None, None, 211.9]
        assert [item["averagePsi"] for item in metrics["items"]] == pressures
