"""Fetch live Flo Detect events using credentials from a .env file."""

import asyncio
from datetime import datetime
import json
import logging
import os
from pathlib import Path
import sys

from aiohttp import ClientSession

from aioflo import async_get_api
from aioflo.errors import FloError

_LOGGER = logging.getLogger()
_REPO_ROOT = Path(__file__).resolve().parent.parent
_MISSING_CREDS = """\
Missing EMAIL or PASSWORD. Create a .env in the repo root:

  EMAIL=you@example.com
  PASSWORD=secret
  USE_SSO=true
"""


def _load_dotenv(path: Path) -> None:
    """Load KEY=VALUE pairs from a .env file without overriding existing vars."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def _as_bool(value: str | None, default: bool = False) -> bool:
    """Interpret a truthy environment string."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _summarize_event(event: dict) -> str:
    """Return a one-line summary of a Flo Detect event."""
    predicted = (event.get("predicted") or {}).get("displayText")
    return (
        f"{event.get('startAt')}  {predicted}  "
        f"{event.get('totalGal')} gal  {event.get('duration')}s"
    )


async def main() -> None:
    """Authenticate and print recent Flo Detect events for every device."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    for candidate in (
        Path.cwd() / ".env",
        _REPO_ROOT / ".env",
        Path(__file__).resolve().parent / ".env",
    ):
        _load_dotenv(candidate)

    email = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")
    if not email or not password:
        sys.stderr.write(_MISSING_CREDS)
        raise SystemExit(1)

    use_sso = _as_bool(os.environ.get("USE_SSO"))
    limit = int(os.environ.get("EVENT_LIMIT", "20"))

    async with ClientSession() as session:
        try:
            api = await async_get_api(email, password, session=session, use_sso=use_sso)

            user_info = await api.user.get_info()
            locations = user_info.get("locations") or []
            if not locations:
                _LOGGER.error("No locations on this account")
                return

            for location in locations:
                location_id = location["id"]
                location_info = await api.location.get_info(location_id)
                loc_name = location_info.get("nickname") or location_id
                devices = location_info.get("devices") or []
                _LOGGER.info(
                    "Location %s (%s): %s device(s)",
                    loc_name,
                    location_id,
                    len(devices),
                )

                for device in devices:
                    mac = device.get("macAddress")
                    name = device.get("nickname") or mac
                    if not mac:
                        _LOGGER.warning("Skipping device without macAddress: %s", name)
                        continue

                    payload = await api.flodetect.get_events(
                        mac,
                        to=datetime.now(),
                        limit=limit,
                    )
                    events = api.flodetect.parse_events(payload)
                    _LOGGER.info("Events for %s (%s): %s", name, mac, len(events))
                    _LOGGER.info(json.dumps(payload, indent=2))
                    for event in events:
                        _LOGGER.info("  %s", _summarize_event(event))

        except FloError as err:
            _LOGGER.error("There was an error: %s", err)


if __name__ == "__main__":
    asyncio.run(main())
