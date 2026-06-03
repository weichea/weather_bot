import pytest

from src.domain.weather import DailyForecast, IntervalForecast, Location, TimeInterval
from src.infrastructure import repository
from src.infrastructure.weather_client import WeatherAPIError
from src.interface import scheduler


class DummyBot:
    def __init__(self):
        self.sent = []

    def send_message(self, chat_id: int, text: str):
        self.sent.append((chat_id, text))


@pytest.mark.asyncio
async def test_blast_job_no_users(monkeypatch):
    monkeypatch.setattr(repository, "get_active_users", lambda: [])
    bot = DummyBot()
    await scheduler._blast_job(bot)
    assert bot.sent == []


@pytest.mark.asyncio
async def test_blast_job_handles_api_error(monkeypatch):
    # Create a fake user with location
    user = repository.UserRecord(
        telegram_id=1,
        chat_id=10,
        locations=[Location(name="TestLoc", latitude=3.0, longitude=101.0)],
        location=Location(name="TestLoc", latitude=3.0, longitude=101.0),
        daily_blast_enabled=True,
        daily_blast_time=None,
        last_sent=None,
    )

    monkeypatch.setattr(repository, "get_active_users", lambda: [user])

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def fetch_forecast(self, name):
            raise WeatherAPIError("down")

    monkeypatch.setattr(
        "src.interface.scheduler.DataGovMyWeatherClient", lambda: FakeClient()
    )

    bot = DummyBot()
    await scheduler._blast_job(bot)
    # API error should be handled; no messages sent
    assert bot.sent == []


def test_format_message():
    pagi = IntervalForecast(TimeInterval.PAGI, "Clear", 5.0, 60, 0.0)
    petang = IntervalForecast(TimeInterval.PETANG, "Cloudy", 8.0, 70, 0.1)
    malam = IntervalForecast(TimeInterval.MALAM, "Rain", 10.0, 80, 5.0)
    df = DailyForecast(
        "Town",
        __import__("datetime").datetime(2026, 6, 1),
        "OK",
        pagi,
        petang,
        malam,
    )
    txt = scheduler.format_forecast_message(df)
    assert "Good morning" in txt
    assert "Pagi:" in txt


@pytest.mark.asyncio
async def test_start_scheduler_accepts_cron_expression() -> None:
    bot = DummyBot()
    scheduler_instance = scheduler.start_scheduler(bot, cron_expression="0 7 * * *")

    try:
        jobs = scheduler_instance.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].trigger.__class__.__name__ == "CronTrigger"
    finally:
        scheduler_instance.shutdown(wait=False)


def test_start_scheduler_rejects_invalid_cron_expression() -> None:
    bot = DummyBot()

    with pytest.raises(ValueError):
        scheduler.start_scheduler(bot, cron_expression="invalid cron")
