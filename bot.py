#!/usr/bin/env python3

from discord.ext import commands
from django import setup

import asyncio
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
setup()

from db.models import Server
from django.conf import settings

class DangoBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=settings.COMMAND_PREFIX, description=settings.DESCRIPTION)

        for extension in settings.INSTALLED_APPS:
            if extension.startswith('plugins.'):
                try:
                    self.load_extension('{ext}.plugin'.format(ext=extension))
                except Exception as e:
                    print('Failed to load extension {ext}: {desc}'.format(ext=extension, desc=e))

    @asyncio.coroutine
    def on_server_join(self, server):
        _server = Server(id=server.id, name=server.name)
        _server.save()

bot = DangoBot()
bot.run(settings.BOT_TOKEN)
