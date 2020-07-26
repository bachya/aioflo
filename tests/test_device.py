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
