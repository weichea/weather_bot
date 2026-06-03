"""Smoke-test the basic repository wiring without external calls."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.infrastructure.config import load_config
from src.infrastructure.weather_client import DataGovMyWeatherClient
from src.main import build_application


def test_load_config_requires_environment_variables(monkeypatch) -> None:
    for name in (
        "TELEGRAM_BOT_TOKEN",
        "DATA_GOV_MY_BASE_URL",
        "DATABASE_PATH",
        "DAILY_CRON",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="Missing required environment variables"):
        load_config()


def test_load_config_reads_required_values(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token-value")
    monkeypatch.setenv("DATA_GOV_MY_BASE_URL", "https://example.com/weather/forecast")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "weather.db"))
    monkeypatch.setenv("DAILY_CRON", "0 7 * * *")

    config = load_config()

    assert config.telegram_bot_token == "token-value"
    assert config.data_gov_my_base_url == "https://example.com/weather/forecast"
    assert config.database_path.endswith("weather.db")
    assert config.daily_cron == "0 7 * * *"


def test_weather_client_respects_base_url() -> None:
    client = DataGovMyWeatherClient(base_url="https://example.com/api")

    assert client.base_url == "https://example.com/api"


def test_build_application_initializes_without_external_api(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token-value")
    monkeypatch.setenv(
        "DATA_GOV_MY_BASE_URL",
        "https://example.com/weather/forecast",
    )
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "weather.db"))
    monkeypatch.setenv("DAILY_CRON", "0 7 * * *")

    config = load_config()
    application = build_application(config, start_scheduler_job=False)

    assert application is not None
    assert application.bot is not None
    assert (tmp_path / "weather.db").exists()
