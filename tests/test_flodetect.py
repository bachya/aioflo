"""Define tests for Flo Detect-related endpoints."""

from datetime import datetime
import json

import aiohttp
import pytest

from aioflo import async_get_api
from aioflo.flodetect import Flodetect

from .common import TEST_EMAIL_ADDRESS, TEST_MAC_ADDRESS, TEST_PASSWORD, load_fixture


@pytest.mark.asyncio
async def test_get_events(aresponses, auth_success_response):
    """Test successfully retrieving Flo Detect events."""
    aresponses.add(
        "api.meetflo.com",
        "/api/v1/users/auth",
        "post",
        aresponses.Response(text=json.dumps(auth_success_response), status=200),
    )

    queries = []

    async def events_handler(request):
        queries.append(dict(request.query))
        return aresponses.Response(
            text=load_fixture("flodetect_events_response.json"), status=200
        )

    aresponses.add(
        "api-gw.meetflo.com", "/api/v2/flodetect/events", "get", events_handler
    )
    aresponses.add(
        "api-gw.meetflo.com", "/api/v2/flodetect/events", "get", events_handler
    )

    to = datetime(2026, 7, 12, 10, 25, 4)

    async with aiohttp.ClientSession() as session:
        api = await async_get_api(TEST_EMAIL_ADDRESS, TEST_PASSWORD, session=session)

        events = await api.flodetect.get_events(TEST_MAC_ADDRESS)
        assert len(events["items"]) == 1
        parsed = api.flodetect.parse_events(events)
        assert len(parsed) == 2
        assert parsed[0]["totalGal"] == 2.35
        assert parsed[0]["duration"] == 158
        assert parsed[0]["startAt"] == "2026-07-12T10:12:03-04:00"
        assert parsed[0]["predicted"]["displayText"] == "Faucet"
        assert parsed[1]["predicted"]["displayText"] == "Shower"
        assert queries[0] == {"macAddress": TEST_MAC_ADDRESS.replace(":", "")}

        events = await api.flodetect.get_events(
            TEST_MAC_ADDRESS,
            to=to,
            limit=20,
        )
        assert len(api.flodetect.parse_events(events)) == 2
        assert queries[1] == {
            "macAddress": TEST_MAC_ADDRESS.replace(":", ""),
            "to": to.isoformat(),
            "limit": "20",
        }


def test_parse_events_empty_payloads():
    """Test parse_events on missing or empty item groups."""
    assert Flodetect.parse_events({}) == []
    assert Flodetect.parse_events({"items": []}) == []
    assert Flodetect.parse_events({"items": [{"macAddress": "123456abcdef"}]}) == []
