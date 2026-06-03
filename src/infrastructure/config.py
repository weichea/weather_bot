"""Runtime configuration support for the weather bot."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    telegram_bot_token: str
    data_gov_my_base_url: str
    database_path: str
    daily_cron: str


def load_config() -> AppConfig:
    """Load and validate runtime configuration from environment variables."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    data_gov_base_url = os.environ.get("DATA_GOV_MY_BASE_URL")
    database_path = os.environ.get("DATABASE_PATH")
    daily_cron = os.environ.get("DAILY_CRON")

    missing = [
        name
        for name, value in (
            ("TELEGRAM_BOT_TOKEN", token),
            ("DATA_GOV_MY_BASE_URL", data_gov_base_url),
            ("DATABASE_PATH", database_path),
            ("DAILY_CRON", daily_cron),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    return AppConfig(
        telegram_bot_token=token,
        data_gov_my_base_url=data_gov_base_url,
        database_path=database_path,
        daily_cron=daily_cron,
    )
