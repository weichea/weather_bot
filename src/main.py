"""Runtime bootstrap for the weather bot application."""

from __future__ import annotations

import logging

from telegram.ext import ApplicationBuilder

from src.infrastructure import config, db
from src.interface.bot import register_handlers
from src.interface.scheduler import start_scheduler

logger = logging.getLogger(__name__)


def build_application(app_config: config.AppConfig, start_scheduler_job: bool = True):
    """Build the Telegram application and wire runtime dependencies."""
    db.set_default_db_path(app_config.database_path)
    db.init_db(app_config.database_path)

    application = ApplicationBuilder().token(app_config.telegram_bot_token).build()
    register_handlers(application)

    if start_scheduler_job:

        async def _post_init(_: object) -> None:
            start_scheduler(application.bot, cron_expression=app_config.daily_cron)

        application.post_init = _post_init

    return application


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app_config = config.load_config()
    application = build_application(app_config)

    logger.info("Starting Telegram application polling")
    application.run_polling()


if __name__ == "__main__":
    main()
