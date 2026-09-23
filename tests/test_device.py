"""Define tests for device-related endpoints."""

import json

import aiohttp
import pytest

from aioflo import async_get_api

from .common import TEST_DEVICE_ID, TEST_EMAIL_ADDRESS, TEST_PASSWORD, load_fixture


@pytest.mark.asyncio
async def test_get_device_info(aresponses, auth_success_response):
    """Test successfully retrieving device info."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/devices/98765",
        "get",
        aresponses.Response(text=load_fixture("device_info_response.json"), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        device_info = await api.device.get_info(TEST_DEVICE_ID)
        assert device_info["fwVersion"] == "6.1.1"
        assert device_info["isConnected"] is True
        assert device_info["macAddress"] == "111111111111"
        assert device_info["nickname"] == "Smart Water Shutoff"


@pytest.mark.asyncio
async def test_device_run_health_test(aresponses, auth_success_response):
    """Test successfully running a health test."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/devices/98765/healthTest/run",
        "post",
        aresponses.Response(text=load_fixture("health_test_response.json"), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        health_test_response = await api.device.run_health_test(TEST_DEVICE_ID)
        assert health_test_response["roundId"] == "123456789-369258147"
        assert health_test_response["deviceId"] == "xxxxx"
        assert health_test_response["status"] == "pending"
        assert health_test_response["type"] == "manual"


@pytest.mark.asyncio
async def test_device_valve_open(aresponses, auth_success_response):
    """Test successfully opening the valve."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/devices/98765",
        "post",
        aresponses.Response(
            text=load_fixture("device_open_valve_response.json"), status=200
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        device_info = await api.device.open_valve(TEST_DEVICE_ID)
        assert device_info["isConnected"] is True
        assert device_info["macAddress"] == "111111111111"
        assert device_info["nickname"] == "Smart Water Shutoff"
        assert device_info["valve"]["target"] == "open"
        assert device_info["valve"]["lastKnown"] == "closed"


@pytest.mark.asyncio
async def test_device_valve_close(aresponses, auth_success_response):
    """Test successfully closing the valve."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/devices/98765",
        "post",
        aresponses.Response(
            text=load_fixture("device_close_valve_response.json"), status=200
        ),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        device_info = await api.device.close_valve(TEST_DEVICE_ID)
        assert device_info["isConnected"] is True
        assert device_info["macAddress"] == "111111111111"
        assert device_info["nickname"] == "Smart Water Shutoff"
        assert device_info["valve"]["target"] == "closed"
        assert device_info["valve"]["lastKnown"] == "open"


@pytest.mark.asyncio
@pytest.mark.parametrize("placeholder", [225, 212, 220, 300])
async def test_get_device_info_normalizes_temperature_placeholder(
    aresponses, auth_success_response, placeholder
):
    """A valve with no temperature sensor reports a placeholder, not a reading.

    Parametrized across the boundary so the check cannot regress to special-casing
    the one value observed in the wild (225).
    """
    device_info_payload = json.loads(load_fixture("device_info_response.json"))
    device_info_payload["telemetry"]["current"]["tempF"] = placeholder

    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/devices/98765",
        "get",
        aresponses.Response(text=json.dumps(device_info_payload), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        device_info = await api.device.get_info(TEST_DEVICE_ID)
        assert device_info["telemetry"]["current"]["tempF"] is None
        # Everything else in the block is untouched.
        assert device_info["telemetry"]["current"]["psi"] == 54.20000076293945


@pytest.mark.asyncio
@pytest.mark.parametrize("reading", [70, 211.9, 33])
async def test_get_device_info_keeps_a_real_temperature(
    aresponses, auth_success_response, reading
):
    """Anything below boiling is a measurement and is passed through unchanged."""
    device_info_payload = json.loads(load_fixture("device_info_response.json"))
    device_info_payload["telemetry"]["current"]["tempF"] = reading

    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/devices/98765",
        "get",
        aresponses.Response(text=json.dumps(device_info_payload), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        device_info = await api.device.get_info(TEST_DEVICE_ID)
        assert device_info["telemetry"]["current"]["tempF"] == reading


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "telemetry",
    [None, {"current": None}, {"current": "225"}],
)
async def test_get_device_info_without_a_temperature_reading(
    aresponses, auth_success_response, telemetry
):
    """No current-telemetry dict means there is nothing to normalize."""
    device_info_payload = json.loads(load_fixture("device_info_response.json"))
    if telemetry is None:
        del device_info_payload["telemetry"]
    else:
        device_info_payload["telemetry"] = telemetry

    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/devices/98765",
        "get",
        aresponses.Response(text=json.dumps(device_info_payload), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        device_info = await api.device.get_info(TEST_DEVICE_ID)
        assert device_info.get("telemetry") == telemetry
        assert device_info["nickname"] == "Smart Water Shutoff"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("valve_method", "fixture_name"),
    [
        ("open_valve", "device_open_valve_response.json"),
        ("close_valve", "device_close_valve_response.json"),
    ],
)
@pytest.mark.parametrize("reading", [225, 212, 211.9, 70])
async def test_valve_command_normalizes_temperature(
    aresponses,
    auth_success_response,
    valve_method,
    fixture_name,
    reading,
):
    """Valve responses carry the same telemetry placeholder as device info."""
    device_info_payload = json.loads(load_fixture(fixture_name))
    current = device_info_payload["telemetry"]["current"]
    current["tempF"] = reading
    psi = current["psi"]

    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )
    aresponses.add(
        "api-gw.meetflo.com",
        "/api/v2/devices/98765",
        "post",
        aresponses.Response(text=json.dumps(device_info_payload), status=200),
    )

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)
        device_info = await getattr(api.device, valve_method)(TEST_DEVICE_ID)
        temperature = device_info["telemetry"]["current"]["tempF"]
        if reading >= 212:
            assert temperature is None
        else:
            assert temperature == reading
        assert device_info["telemetry"]["current"]["psi"] == psi
