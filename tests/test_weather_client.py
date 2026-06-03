from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.infrastructure.weather_client import (
    STATION_REFERENCE_FILE,
    DataGovMyWeatherClient,
)


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_fetch_forecast_parses_response_list() -> None:
    client = DataGovMyWeatherClient(base_url="https://example.com/weather/forecast")
    client.client = AsyncMock()
    today = datetime.now().date().isoformat()
    client.client.get.return_value = DummyResponse(
        [
            {
                "location": {"location_id": "Ds001", "location_name": "Langkawi"},
                "date": today,
                "morning_forecast": "Sunny",
                "afternoon_forecast": "Cloudy",
                "night_forecast": "Rain",
                "summary_forecast": "Mixed weather",
            }
        ]
    )

    forecast = await client.fetch_forecast("Langkawi")

    assert forecast.location_name == "Langkawi"
    assert forecast.pagi.summary == "Sunny"
    assert forecast.petang.summary == "Cloudy"
    assert forecast.malam.summary == "Rain"
    assert forecast.general_forecast == "Mixed weather"


@pytest.mark.asyncio
async def test_fetch_forecast_for_coordinates_uses_nearest_station() -> None:
    client = DataGovMyWeatherClient(base_url="https://example.com/weather/forecast")
    client.client = AsyncMock()
    today = datetime.now().date().isoformat()
    client.client.get.return_value = DummyResponse(
        [
            {
                "location": {"location_id": "St001", "location_name": "Kuala Lumpur"},
                "date": today,
                "morning_forecast": "Sunny",
                "afternoon_forecast": "Cloudy",
                "night_forecast": "Rain",
                "summary_forecast": "Mixed weather",
            }
        ]
    )

    forecast = await client.fetch_forecast_for_coordinates(3.14, 101.69)

    assert forecast.location_name == "Kuala Lumpur"
    assert client.client.get.call_args.kwargs["params"]["contains"].startswith(
        "Kuala Lumpur"
    )


def test_load_station_references_from_file() -> None:
    client = DataGovMyWeatherClient()
    references = client._load_station_references()

    assert references
    assert any(ref.location_name == "Kuala Lumpur" for ref in references)
    assert any(ref.location_name == "Langkawi" for ref in references)
    assert any(ref.location_name == "Senai" for ref in references)


def test_load_location_index_contains_senai() -> None:
    client = DataGovMyWeatherClient()
    locations = client._load_location_index()

    assert locations
    assert any(location["location_name"] == "Senai" for location in locations)


def test_async_client_follows_redirects(monkeypatch) -> None:
    created = {}

    class FakeAsyncClient:
        def __init__(self, timeout=None, follow_redirects=False):
            created["timeout"] = timeout
            created["follow_redirects"] = follow_redirects

        async def aclose(self):
            pass

    monkeypatch.setattr(
        "src.infrastructure.weather_client.httpx.AsyncClient",
        FakeAsyncClient,
    )

    client = DataGovMyWeatherClient()

    async def run():
        async with client:
            assert created["follow_redirects"] is True
            assert created["timeout"] == client.TIMEOUT

    import asyncio

    asyncio.run(run())


def test_weather_stations_file_contains_kulai() -> None:
    raw_data = json.loads(Path(STATION_REFERENCE_FILE).read_text())

    assert any(entry["location_name"] == "Kulai" for entry in raw_data)
