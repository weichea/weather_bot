# Malaysian Farming Weather Telegram Bot

A small Python bot that registers Telegram users, persists their location in SQLite, and sends daily weather blasts.

## Runtime setup

Create a Python virtual environment and install dependencies.

```bash
python -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
```

## Required environment variables

The application reads configuration from environment variables at startup:

- `TELEGRAM_BOT_TOKEN` — Telegram bot API token
- `DATA_GOV_MY_BASE_URL` — Base URL for the weather API, e.g. `https://api.data.gov.my/weather/forecast`
- `DATABASE_PATH` — SQLite database file path, e.g. `data/weather_bot.db`
- `DAILY_CRON` — Daily scheduler cron expression, e.g. `0 7 * * *`

## Run the bot

From the repository root:

```bash
export TELEGRAM_BOT_TOKEN="<token>"
export DATA_GOV_MY_BASE_URL="https://api.data.gov.my/weather/forecast"
export DATABASE_PATH="data/weather_bot.db"
export DAILY_CRON="0 7 * * *"

./venv/bin/python src/main.py
```

The runtime bootstrap validates that the required variables are set before starting.

## Bot commands

The Telegram bot supports these commands:

- `/start` — register and send your location for daily weather updates.
- `/forecast` — request today's forecast immediately using your saved location.
- `/location` — show your saved coordinates.
- `/coords` — show your saved coordinates.
- `/stop` — unsubscribe from daily weather blasts.
