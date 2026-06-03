from unittest import mock

import pytest

from src.domain.weather import DailyForecast, IntervalForecast, Location, TimeInterval
from src.interface import bot as bot_module


class DummyMessage:
    def __init__(self):
        self.text = None
        self.location = None

    async def reply_text(self, text):
        self._replied = text


class DummyUpdate:
    def __init__(self):
        self.effective_user = mock.MagicMock()
        self.effective_user.id = 123
        self.effective_chat = mock.MagicMock()
        self.effective_chat.id = 456
        self.message = DummyMessage()


class DummyContext:
    pass


@pytest.mark.asyncio
async def test_start_reply():
    update = DummyUpdate()
    ctx = DummyContext()

    await bot_module.start(update, ctx)
    assert hasattr(update.message, "_replied")
    assert "Please share your GPS location" in update.message._replied


@pytest.mark.asyncio
async def test_help_reply():
    update = DummyUpdate()
    ctx = DummyContext()

    await bot_module.help_command(update, ctx)
    assert "/start" in update.message._replied


@pytest.mark.asyncio
async def test_stop_calls_disable_user(monkeypatch):
    update = DummyUpdate()
    ctx = DummyContext()

    called = {}

    def fake_disable(telegram_id):
        called["id"] = telegram_id

    monkeypatch.setattr(
        "src.infrastructure.repository.disable_user_record",
        fake_disable,
    )

    await bot_module.stop(update, ctx)
    assert called["id"] == update.effective_user.id


@pytest.mark.asyncio
async def test_location_handler_saves(monkeypatch):
    update = DummyUpdate()
    ctx = DummyContext()
    # attach a fake location
    loc = mock.MagicMock()
    loc.latitude = 3.14
    loc.longitude = 101.69
    update.message.location = loc

    saved = {}

    def fake_add_or_update_user(**kwargs):
        saved.update(kwargs)

    monkeypatch.setattr(
        "src.infrastructure.repository.save_user_location", fake_add_or_update_user
    )

    await bot_module.location_handler(update, ctx)
    assert saved["latitude"] == 3.14
    assert saved["longitude"] == 101.69


@pytest.mark.asyncio
async def test_text_handler_parses_typed_coords(monkeypatch):
    update = DummyUpdate()
    ctx = DummyContext()
    update.message.text = "3.14,101.69"

    saved = {}

    def fake_add_or_update_user(**kwargs):
        saved.update(kwargs)

    monkeypatch.setattr(
        "src.infrastructure.repository.save_user_location", fake_add_or_update_user
    )

    await bot_module.text_handler(update, ctx)
    assert saved["latitude"] == 3.14
    assert saved["longitude"] == 101.69


@pytest.mark.asyncio
async def test_forecast_handler_uses_coordinate_lookup(monkeypatch):
    update = DummyUpdate()
    ctx = DummyContext()
    update.message.text = "/forecast"

    user = mock.MagicMock()
    user.location = Location(name="", latitude=3.14, longitude=101.69)

    monkeypatch.setattr(
        "src.infrastructure.repository.get_user",
        lambda telegram_id: user,
    )

    forecast = DailyForecast(
        location_name="Kuala Lumpur",
        date=__import__("datetime").datetime(2026, 6, 1),
        general_forecast="No rain",
        pagi=IntervalForecast(TimeInterval.PAGI, "Clear", 0.0, 0, 0.0),
        petang=IntervalForecast(TimeInterval.PETANG, "Hot", 0.0, 0, 0.0),
        malam=IntervalForecast(TimeInterval.MALAM, "Cool", 0.0, 0, 0.0),
    )

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def fetch_forecast_for_coordinates(self, lat, lon):
            assert lat == 3.14
            assert lon == 101.69
            return forecast

    monkeypatch.setattr(
        "src.interface.bot.DataGovMyWeatherClient",
        lambda: FakeClient(),
    )

    await bot_module.forecast(update, ctx)
    assert "Weather for" in update.message._replied
    assert "Kuala Lumpur" in update.message._replied


@pytest.mark.asyncio
async def test_forecast_handler_prompts_for_location(monkeypatch):
    update = DummyUpdate()
    ctx = DummyContext()

    monkeypatch.setattr(
        "src.infrastructure.repository.get_user",
        lambda telegram_id: None,
    )

    await bot_module.forecast(update, ctx)
    assert "Please send your location" in update.message._replied


@pytest.mark.asyncio
async def test_show_saved_location_reports_coords(monkeypatch):
    update = DummyUpdate()
    ctx = DummyContext()

    user = mock.MagicMock()
    user.location = Location(name="", latitude=3.14, longitude=101.69)

    monkeypatch.setattr(
        "src.infrastructure.repository.get_user",
        lambda telegram_id: user,
    )

    await bot_module.show_saved_location(update, ctx)
    assert "Your saved location is" in update.message._replied
    assert "3.14, 101.69" in update.message._replied


@pytest.mark.asyncio
async def test_show_saved_location_prompts_for_location(monkeypatch):
    update = DummyUpdate()
    ctx = DummyContext()

    monkeypatch.setattr(
        "src.infrastructure.repository.get_user",
        lambda telegram_id: None,
    )

    await bot_module.show_saved_location(update, ctx)
    assert "No saved location found" in update.message._replied
