# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`aioflo` is a Python 3, asyncio-friendly client library for the Flo by Moen Smart Water Detector API. It is published to PyPI with calendar versioning (`YYYY.MM.N`) and managed with Poetry.

## Commands

```sh
script/setup                 # Install poetry, dependencies, and pre-commit hooks
script/test                  # Run pytest with coverage (same as CI)
pytest tests                 # Run all tests
pytest tests/test_water.py::test_get_consumption_info   # Run a single test
pre-commit run --all-files   # Lint: black, isort, flake8, mypy, bandit, pydocstyle, pyupgrade, codespell
```

`pytest-asyncio` runs in `auto` mode (configured in `pyproject.toml`), so async test functions need no decorator.

## Branches and releases

- `dev` is the default branch; `main` only receives merges from `dev` at release time via `script/release` (which also bumps the version in `pyproject.toml` and tags). Pre-commit blocks direct commits to `dev`/`master`, so work on feature branches.

## Architecture

The package is a thin async wrapper around two Flo hosts:

- `api.meetflo.com/api/v1` — authentication only (`API.async_authenticate` in `aioflo/api.py`)
- `api-gw.meetflo.com/api/v2` — everything else (`API_V2_BASE` in `aioflo/const.py`)

`aioflo/api.py` is the hub. `async_get_api(username, password)` builds an `API` object and authenticates. `API._request` handles browser-mimicking headers, the bearer token, automatic re-authentication when the token expires, and wraps all HTTP errors in `RequestError` (from `aioflo/errors.py`). It checks `raise_for_status()` before JSON-parsing so non-JSON error bodies still surface as `RequestError`.

Each endpoint group (`alarm.py`, `device.py`, `location.py`, `presence.py`, `user.py`, `water.py`) is a small class that receives the bound `API._request` coroutine in its constructor — they hold no other state. They are attached to `API` as `api.alarm`, `api.device`, etc. Exception: `api.user` is `None` until authentication completes, because `User` needs the user ID from the auth response.

Two distinct device identifiers are used by the Flo API:

- **device UUID** (`id`) — used by `/devices/{id}` endpoints (`device.py`)
- **MAC address** — used by `/water` endpoints (`water.py`), sent with `:` separators stripped

Both appear in `location_info["devices"]` and in `api.device.get_info()` responses.

`get_consumption_info` is location-wide unless `device_mac_address` is passed (same `macAddress` query param as `get_metrics`). Omitting it preserves the aggregate used by single-device locations.

## Downstream

The main consumer is Home Assistant's built-in `flo` integration (`homeassistant/components/flo`, codeowner `@dmulcahey`). Core pins `aioflo==2021.11.0` in `manifest.json`. Its coordinator calls `get_consumption_info(location_id, start, end)` with no MAC, so multi-device locations report the location total on every device. A core pin bump (and passing `device_mac_address=self.mac_address`) requires a new release on PyPI under the existing `aioflo` name — HA will not pick up a renamed fork.

## Tests

Tests mock HTTP with `aresponses` against canned JSON in `tests/fixtures/` (loaded via `load_fixture` in `tests/common.py`). Every test must mock the v1 auth POST (`api.meetflo.com` `/api/v1/users/auth`) first, since `async_get_api` authenticates immediately; shared constants and the `auth_success_response` fixture live in `tests/common.py` and `tests/conftest.py`. Each `aresponses.add` matches exactly one request unless `repeat=` is given — add one mock per expected call.
