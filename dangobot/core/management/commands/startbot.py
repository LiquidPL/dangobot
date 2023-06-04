from django.core.management.base import BaseCommand
from django.conf import settings

from discord.utils import _ColourFormatter, stream_supports_colour

import os
import logging
import logging.handlers

from dangobot.core.bot import DangoBot


class Command(BaseCommand):
    help = "Starts the bot"

    def __init__(self):
        super().__init__()

        self.setup_logging()
        self.bot = DangoBot()

    def setup_logging(self):
        os.makedirs("logs/", exist_ok=True)

        logger = logging.getLogger()

        logger.setLevel(logging.INFO)

        consoleHandler = logging.StreamHandler()
        if stream_supports_colour(consoleHandler.stream):
            consoleHandler.setFormatter(_ColourFormatter())
        else:
            consoleHandler.setFormatter(
                logging.Formatter(
                    "{asctime} {levelname:<8} {name} {message}",
                    "%Y-%m-%d %H:%M:%S",
                    style="{",
                )
            )
        logger.addHandler(consoleHandler)

        fileHandler = logging.handlers.RotatingFileHandler(
            filename="logs/dangobot.log",
            encoding="utf-8",
            maxBytes=32 * 1024 * 1024,
            backupCount=5,
        )
        fileHandler.setFormatter(
            logging.Formatter(
                "{asctime} {levelname:<8} {name} {message}",
                "%Y-%m-%d %H:%M:%S",
                style="{",
            )
        )
        logger.addHandler(fileHandler)

    def handle(self, *args, **options):
        self.bot.run(settings.BOT_TOKEN, log_handler=None)
