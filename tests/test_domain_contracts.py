"""Verify weather-domain contracts and invariants."""

from __future__ import annotations

from datetime import datetime

from src.domain.weather import (
    DailyForecast,
    IntervalForecast,
    Location,
    TimeInterval,
    WeatherAPIError,
)


def _interval_forecast(interval: TimeInterval) -> IntervalForecast:
    return IntervalForecast(
        interval=interval,
        summary="Partly cloudy",
        wind_speed=12.5,
        humidity=84,
        rain=1.2,
    )


def test_time_interval_labels_match_expected_terms() -> None:
    assert TimeInterval.PAGI.value == "Pagi"
    assert TimeInterval.PETANG.value == "Petang"
    assert TimeInterval.MALAM.value == "Malam"


def test_weather_domain_models_are_frozen_and_composable() -> None:
    pagi = _interval_forecast(TimeInterval.PAGI)
    petang = _interval_forecast(TimeInterval.PETANG)
    malam = _interval_forecast(TimeInterval.MALAM)
    forecast = DailyForecast(
        location_name="Kuala Lumpur",
        date=datetime(2026, 6, 1),
        general_forecast="Mostly dry",
        pagi=pagi,
        petang=petang,
        malam=malam,
    )

    assert forecast.location_name == "Kuala Lumpur"
    assert forecast.pagi.interval is TimeInterval.PAGI
    assert forecast.petang.summary == "Partly cloudy"
    assert forecast.malam.rain == 1.2

    location = Location(name="Seremban", latitude=2.7297, longitude=101.9381)
    assert location.name == "Seremban"
    assert location.latitude == 2.7297
    assert location.longitude == 101.9381

    assert DailyForecast.__dataclass_params__.frozen is True
    assert IntervalForecast.__dataclass_params__.frozen is True
    assert Location.__dataclass_params__.frozen is True


def test_weather_api_error_is_a_domain_exception() -> None:
    assert issubclass(WeatherAPIError, Exception)
