"""Telegram bot handlers for user flows.

Handlers are intentionally thin: they accept Telegram updates and delegate
persistence to `src.infrastructure.db` and domain validation to `src.domain`.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, MessageHandler

from src.infrastructure.weather_client import DataGovMyWeatherClient, WeatherAPIError
from src.interface.scheduler import format_forecast_message

# Compatibility shim for different PTB versions: try old `Filters`, fall back
# to the `filters` module which exposes uppercase constants.
try:  # pragma: no cover - compatibility shim
    from telegram.ext import Filters as _PTB_Filters

    FILTERS_LOCATION = _PTB_Filters.location
    FILTERS_TEXT = _PTB_Filters.text
    FILTERS_COMMAND = _PTB_Filters.command
except Exception:  # pragma: no cover - compatibility shim
    from telegram.ext import filters as _PTB_Filters

    FILTERS_LOCATION = _PTB_Filters.LOCATION
    FILTERS_TEXT = _PTB_Filters.TEXT
    FILTERS_COMMAND = _PTB_Filters.COMMAND

from src.infrastructure import repository

logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message and ask the user to share their location."""
    chat_id = update.effective_chat.id
    text = (
        "Selamat datang! Please share your GPS location so I can send daily "
        "weather updates. You can use the attachment (paperclip) -> Location "
        "in Telegram, or type coordinates as `lat, lon`."
    )
    await update.message.reply_text(text)
    logger.info("Sent start prompt to chat_id=%s", chat_id)


async def help_command(update: Update, context: CallbackContext) -> None:
    """Show help information."""
    await update.message.reply_text(
        "/start - register and receive location prompt\n"
        "/forecast - get today's forecast immediately\n"
        "/location - show your saved coordinates\n"
        "/coords - show your saved coordinates\n"
        "/stop - opt out of daily blasts\n"
        "Share a location or type coordinates as `lat, lon` to register."
    )


async def forecast(update: Update, context: CallbackContext) -> None:
    """Return today's forecast for the registered user location."""
    telegram_id = update.effective_user.id
    user = repository.get_user(telegram_id)

    if not user or not user.location:
        await update.message.reply_text(
            "Please send your location or typed coordinates first with /start. "
            "Then use /forecast to get a weather update."
        )
        return

    try:
        async with DataGovMyWeatherClient() as client:
            if (
                user.location.latitude is not None
                and user.location.longitude is not None
            ):
                forecast_data = await client.fetch_forecast_for_coordinates(
                    user.location.latitude,
                    user.location.longitude,
                )
            elif user.location.name:
                forecast_data = await client.fetch_forecast(user.location.name)
            else:
                await update.message.reply_text(
                    "Unable to resolve your saved location. Please send location again."
                )
                return

        await update.message.reply_text(format_forecast_message(forecast_data))
        logger.info("Provided forecast for user %s", telegram_id)
    except WeatherAPIError as exc:
        logger.warning(
            "Weather API failure for /forecast user %s: %s",
            telegram_id,
            exc,
        )
        await update.message.reply_text(
            "Sorry, I couldn't fetch the forecast right now. Please try again later."
        )


async def stop(update: Update, context: CallbackContext) -> None:
    """Disable daily blasts for the user."""
    telegram_id = update.effective_user.id
    try:
        repository.disable_user_record(telegram_id)
        await update.message.reply_text(
            "You have been unsubscribed from daily updates."
        )
        logger.info("Disabled user %s", telegram_id)
    except Exception as exc:  # pragma: no cover - defensive boundary
        logger.exception("Failed to disable user %s: %s", telegram_id, exc)
        await update.message.reply_text("Sorry, an error occurred while unsubscribing.")


async def location_handler(update: Update, context: CallbackContext) -> None:
    """Handle incoming location messages from Telegram."""
    msg = update.message
    if not msg or not msg.location:
        return

    lat = msg.location.latitude
    lon = msg.location.longitude
    telegram_id = update.effective_user.id
    chat_id = update.effective_chat.id

    try:
        repository.save_user_location(
            telegram_id=telegram_id,
            chat_id=chat_id,
            latitude=lat,
            longitude=lon,
            location_name=None,
        )
        await update.message.reply_text(
            "Location saved. You'll receive daily morning weather updates."
        )
        logger.info("Saved location for user %s: %s,%s", telegram_id, lat, lon)
    except Exception as exc:  # pragma: no cover - shield infra errors
        logger.exception("Failed to save location for %s: %s", telegram_id, exc)
        await update.message.reply_text(
            "Failed to save location. Please try again later."
        )


async def text_handler(update: Update, context: CallbackContext) -> None:
    """Handle plain text messages, accept typed coordinates as `lat, lon`."""
    text = (update.message and update.message.text) or ""
    text = text.strip()
    if not text:
        return

    # Find numeric tokens (floats/ints) in the message. Accept formats like
    # "3.139, 101.686" or "3.139 101.686" or messages with trailing text.
    nums = re.findall(r"[-+]?\d+(?:\.\d+)?", text)
    if len(nums) < 2:
        return

    try:
        lat = float(nums[0])
        lon = float(nums[1])
    except (ValueError, TypeError):
        return

    # Basic validation
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        await update.message.reply_text(
            "Coordinates out of range. Please provide valid lat, lon values."
        )
        return

    telegram_id = update.effective_user.id
    chat_id = update.effective_chat.id
    try:
        repository.save_user_location(
            telegram_id=telegram_id,
            chat_id=chat_id,
            latitude=lat,
            longitude=lon,
            location_name=None,
        )
        await update.message.reply_text("Coordinates saved. Thank you!")
        logger.info("Saved typed coords for %s: %s,%s", telegram_id, lat, lon)
    except Exception:  # pragma: no cover - defensive boundary
        await update.message.reply_text(
            "Failed to save coordinates. Please try again later."
        )


async def show_saved_location(update: Update, context: CallbackContext) -> None:
    """Display the user's currently saved coordinates."""
    telegram_id = update.effective_user.id
    user = repository.get_user(telegram_id)

    if not user or not user.location:
        await update.message.reply_text(
            "No saved location found. Please send your location with /start "
            "or type coordinates as `lat, lon`."
        )
        return

    location = user.location
    location_name = f" ({location.name})" if location.name else ""
    await update.message.reply_text(
        "Your saved location is"
        f"{location_name}: {location.latitude}, {location.longitude}."
    )


def register_handlers(dispatcher: Any) -> None:
    """Register command and message handlers on a dispatcher-like object.

    This function keeps wiring centralized and testable. The `dispatcher`
    object is expected to implement `add_handler` similar to PTB's `Dispatcher`.
    """
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("forecast", forecast))
    dispatcher.add_handler(CommandHandler("location", show_saved_location))
    dispatcher.add_handler(CommandHandler("coords", show_saved_location))
    dispatcher.add_handler(CommandHandler("stop", stop))
    dispatcher.add_handler(
        MessageHandler(FILTERS_LOCATION, location_handler),
    )
    dispatcher.add_handler(
        MessageHandler(FILTERS_TEXT & ~FILTERS_COMMAND, text_handler),
    )
