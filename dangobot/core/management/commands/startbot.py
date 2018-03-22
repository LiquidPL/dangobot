from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from ...bot import DangoBot


class Command(BaseCommand):
    help = 'Starts the bot'

    def __init__(self):
        self.bot = DangoBot()

    def handle(self, *args, **options):
        self.bot.run(settings.BOT_TOKEN)
