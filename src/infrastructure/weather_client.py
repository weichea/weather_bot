"""Asynchronous weather API client for data.gov.my integration."""

import json
from dataclasses import dataclass
from datetime import datetime
from math import acos, cos, radians, sin
from pathlib import Path
from typing import Any

import httpx

from src.domain.weather import (
    DailyForecast,
    IntervalForecast,
    TimeInterval,
    WeatherAPIError,
)


@dataclass(frozen=True)
class StationReference:
    """A simple reference used to resolve the nearest forecast location."""

    location_name: str
    latitude: float
    longitude: float


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
STATION_REFERENCE_FILE = DATA_DIR / "weather_stations.json"
LOCATION_INDEX_FILE = DATA_DIR / "weather_location_index.json"


class DataGovMyWeatherClient:
    """Async client for data.gov.my weather forecast API."""

    BASE_URL = "https://api.data.gov.my/weather/forecast"
    TIMEOUT = httpx.Timeout(10.0)
    STATION_REFERENCES: tuple[StationReference, ...] | None = None
    LOCATION_INDEX: list[dict[str, str]] | None = None

    def __init__(self, base_url: str | None = None) -> None:
        """Initialize the weather client."""
        self.client: httpx.AsyncClient | None = None
        self.base_url = base_url or self.BASE_URL

    async def __aenter__(self) -> "DataGovMyWeatherClient":
        """Async context manager entry."""
        self.client = httpx.AsyncClient(
            timeout=self.TIMEOUT,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def fetch_forecast(self, location_name: str) -> DailyForecast:
        """
        Fetch weather forecast for a specific location name.

        Uses the data.gov.my `contains` query syntax on nested location fields.
        """
        if not self.client:
            raise WeatherAPIError("Client not initialized. Use async context manager.")

        params = {
            "contains": f"{location_name}@location__location_name",
            "limit": 7,
        }

        try:
            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            return self._parse_forecast(data, location_name)
        except httpx.RequestError as e:
            raise WeatherAPIError(f"Network error fetching forecast: {e}") from e
        except httpx.HTTPStatusError as e:
            raise WeatherAPIError(
                f"API returned {e.response.status_code}: {e.response.text}"
            ) from e
        except (json.JSONDecodeError, ValueError) as e:
            raise WeatherAPIError(f"Failed to parse API response: {e}") from e

    async def fetch_forecast_for_coordinates(
        self, latitude: float, longitude: float
    ) -> DailyForecast:
        """Fetch weather forecast for the nearest known station to coordinates."""
        nearest_station = self._resolve_nearest_station(latitude, longitude)
        return await self.fetch_forecast(nearest_station.location_name)

    def _resolve_nearest_station(
        self, latitude: float, longitude: float
    ) -> StationReference:
        """Choose the nearest predefined station reference for the given coordinates."""
        station_references = self._load_station_references()
        return min(
            station_references,
            key=lambda station: self._haversine_distance(
                latitude, longitude, station.latitude, station.longitude
            ),
        )

    @classmethod
    def _load_station_references(cls) -> tuple[StationReference, ...]:
        """Load station references from the external JSON file."""
        if cls.STATION_REFERENCES is None:
            cls.STATION_REFERENCES = tuple(cls._read_station_reference_file())
        return cls.STATION_REFERENCES

    @classmethod
    def _load_location_index(cls) -> list[dict[str, str]]:
        """Load the complete location index from the external JSON file."""
        if cls.LOCATION_INDEX is None:
            cls.LOCATION_INDEX = cls._read_location_index_file()
        return cls.LOCATION_INDEX

    @staticmethod
    def _read_location_index_file() -> list[dict[str, str]]:
        """Read the complete location index from the JSON data file."""
        if not LOCATION_INDEX_FILE.exists():
            raise WeatherAPIError(
                f"Location index file not found: {LOCATION_INDEX_FILE}"
            )

        try:
            raw_data = json.loads(LOCATION_INDEX_FILE.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise WeatherAPIError(f"Failed to load location index: {exc}") from exc

        locations = []
        for entry in raw_data:
            try:
                locations.append(
                    {
                        "location_id": str(entry["location_id"]),
                        "location_name": str(entry["location_name"]),
                    }
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise WeatherAPIError(f"Invalid location index entry: {entry}") from exc
        return locations

    @staticmethod
    def _read_station_reference_file() -> list[StationReference]:
        """Read station reference entries from the JSON data file."""
        if not STATION_REFERENCE_FILE.exists():
            raise WeatherAPIError(
                f"Station reference file not found: {STATION_REFERENCE_FILE}"
            )

        try:
            raw_data = json.loads(STATION_REFERENCE_FILE.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise WeatherAPIError(f"Failed to load station references: {exc}") from exc

        references = []
        for entry in raw_data:
            location_name = entry.get("location_name")
            latitude = entry.get("latitude")
            longitude = entry.get("longitude")

            if location_name is None or latitude is None or longitude is None:
                continue

            try:
                references.append(
                    StationReference(
                        location_name=str(location_name),
                        latitude=float(latitude),
                        longitude=float(longitude),
                    )
                )
            except (TypeError, ValueError) as exc:
                raise WeatherAPIError(
                    f"Invalid station reference entry: {entry}"
                ) from exc

        return references

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Compute the great-circle distance between two WGS84 coordinates."""
        lat1_r = radians(lat1)
        lon1_r = radians(lon1)
        lat2_r = radians(lat2)
        lon2_r = radians(lon2)
        return acos(
            max(
                -1.0,
                min(
                    1.0,
                    sin(lat1_r) * sin(lat2_r)
                    + cos(lat1_r) * cos(lat2_r) * cos(lon2_r - lon1_r),
                ),
            )
        )

    def _parse_forecast(
        self, data: list[dict[str, Any]], location_name: str
    ) -> DailyForecast:
        """
        Parse raw API response into DailyForecast domain model.

        The data.gov.my weather forecast endpoint returns a list of forecast items
        ordered by date. We select today's forecast when available, otherwise the
        first item in the response.
        """
        if not isinstance(data, list) or not data:
            raise WeatherAPIError("Weather API returned no forecast data.")

        today = datetime.now().date().isoformat()
        item = next((entry for entry in data if entry.get("date") == today), data[0])

        location = item.get("location", {}) or {}
        resolved_location_name = location.get("location_name") or location_name
        date_str = item.get("date", "")

        try:
            forecast_date = datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            forecast_date = datetime.now()

        return DailyForecast(
            location_name=resolved_location_name,
            date=forecast_date,
            general_forecast=item.get("summary_forecast", "No forecast available"),
            pagi=self._build_interval(
                item.get("morning_forecast", "Unknown"), TimeInterval.PAGI
            ),
            petang=self._build_interval(
                item.get("afternoon_forecast", "Unknown"), TimeInterval.PETANG
            ),
            malam=self._build_interval(
                item.get("night_forecast", "Unknown"), TimeInterval.MALAM
            ),
        )

    def _build_interval(
        self, summary: str, interval_type: TimeInterval
    ) -> IntervalForecast:
        """Build an interval forecast using the API summary value."""
        return IntervalForecast(
            interval=interval_type,
            summary=str(summary),
            wind_speed=0.0,
            humidity=0,
            rain=0.0,
        )
