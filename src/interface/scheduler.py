"""Scheduler wiring to send daily weather blasts to active users.

This module wires the AsyncIO scheduler to load active users from the
infrastructure repository, call the `DataGovMyWeatherClient` ingestion client,
format messages, and send them via the provided Telegram `bot` instance.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.infrastructure import repository
from src.infrastructure.weather_client import DataGovMyWeatherClient, WeatherAPIError

logger = logging.getLogger(__name__)

MALAYSIA_TZ = ZoneInfo("Asia/Kuala_Lumpur")


async def _send_message_async(bot: Any, chat_id: int, text: str) -> None:
    """Send a message using bot.sync or async send_message APIs."""
    send = getattr(bot, "send_message")
    if asyncio.iscoroutinefunction(send):
        await send(chat_id=chat_id, text=text)
        return

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, send, chat_id, text)


async def _blast_job(bot: Any) -> None:
    """Job executed by the scheduler to blast all active users.

    The job loads active users, queries the weather API for each, and sends a
    formatted message. Exceptions for individual users are recorded but do not
    halt the job.
    """
    users = repository.get_active_users()
    if not users:
        logger.info("No active users to blast")
        return

    async with DataGovMyWeatherClient() as client:
        for user in users:
            if not user.location:
                logger.debug("Skipping user %s: no location", user.telegram_id)
                continue

            location_name = user.location.name or ""
            try:
                # Prefer exact coordinate lookup first, then fall back to the
                # saved location name for broader matches.
                if (
                    user.location.latitude is not None
                    and user.location.longitude is not None
                ):
                    forecast = await client.fetch_forecast_for_coordinates(
                        user.location.latitude,
                        user.location.longitude,
                    )
                elif location_name:
                    forecast = await client.fetch_forecast(location_name)
                else:
                    logger.debug(
                        "Skipping user %s: no location information", user.telegram_id
                    )
                    continue

                text = format_forecast_message(forecast)
                await _send_message_async(bot, user.chat_id, text)
                repository.update_last_sent(user.telegram_id, when=datetime.now())
            except WeatherAPIError as exc:
                logger.warning("WeatherAPIError for user %s: %s", user.telegram_id, exc)
            except Exception as exc:  # pragma: no cover - external send errors
                logger.exception(
                    "Failed to send blast to %s: %s",
                    user.telegram_id,
                    exc,
                )


def format_forecast_message(forecast: Any) -> str:
    """Format `DailyForecast` into a user-friendly message."""
    date_str = forecast.date.date()
    lines = [f"Good morning! Weather for {forecast.location_name} ({date_str})"]
    lines.append(f"General: {forecast.general_forecast}")

    def fmt_interval(iv):
        return (
            f"{iv.interval.value}: {iv.summary} — Rain {iv.rain:.1f} mm, "
            f"Wind {iv.wind_speed:.1f} km/h, Humidity {iv.humidity}%"
        )

    lines.append(fmt_interval(forecast.pagi))
    lines.append(fmt_interval(forecast.petang))
    lines.append(fmt_interval(forecast.malam))

    return "\n".join(lines)


def start_scheduler(bot: Any, cron_expression: str = "0 7 * * *") -> AsyncIOScheduler:
    """Start and return an AsyncIOScheduler configured for Malaysia time.

    The returned scheduler is started and can be shut down by the caller.
    """
    scheduler = AsyncIOScheduler(timezone=MALAYSIA_TZ)
    trigger = CronTrigger.from_crontab(cron_expression, timezone=MALAYSIA_TZ)
    scheduler.add_job(
        lambda: asyncio.create_task(_blast_job(bot)),
        trigger=trigger,
        id="daily_blast",
    )
    scheduler.start()
    logger.info(
        "Scheduler started for daily blast at %s %s",
        cron_expression,
        MALAYSIA_TZ,
    )
    return scheduler
