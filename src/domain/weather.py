"""Domain models and exceptions for weather data."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TimeInterval(str, Enum):
    """Time interval labels in Malaysian context."""

    PAGI = "Pagi"  # Morning
    PETANG = "Petang"  # Afternoon
    MALAM = "Malam"  # Evening


class WeatherAPIError(Exception):
    """Raised when weather API fails to fetch or parse data."""

    pass


@dataclass(frozen=True)
class IntervalForecast:
    """Forecast for a specific time interval."""

    interval: TimeInterval
    summary: str
    wind_speed: float  # km/h
    humidity: int  # percentage
    rain: float  # mm


@dataclass(frozen=True)
class DailyForecast:
    """Daily weather forecast for a location."""

    location_name: str
    date: datetime
    general_forecast: str
    pagi: IntervalForecast
    petang: IntervalForecast
    malam: IntervalForecast


@dataclass(frozen=True)
class Location:
    """Geographic location."""

    name: str
    latitude: float
    longitude: float
