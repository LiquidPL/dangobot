from django.core.management.base import BaseCommand
from django.conf import settings

import logging
import os
import yaml

from dangobot.core.bot import DangoBot


class Command(BaseCommand):
    help = "Starts the bot"

    def __init__(self):
        with open(
            os.path.join(settings.BASE_DIR, "dangobot", "logging.yml"), "r"
        ) as config_file:
            logging_config = yaml.safe_load(config_file)

        if settings.DEBUG:
            for k, v in logging_config["loggers"].items():
                logging_config["loggers"][k]["handlers"].append("console")

        logging.config.dictConfig(logging_config)

        self.bot = DangoBot()

    def handle(self, *args, **options):
        self.bot.run(settings.BOT_TOKEN)
