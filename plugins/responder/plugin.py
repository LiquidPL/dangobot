from discord.ext import commands
from discord.ext.commands.view import StringView

from .models import Command

import asyncio
import functools

class Responder:
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        view = StringView(message.content)
        prefix = await self.bot._get_prefix(message)
        invoked_prefix = prefix

        if not isinstance(prefix, (tuple, list)):
            if not view.skip_string(prefix):
                return
        else:
            invoked_prefix = discord.utils.find(view.skip_string, prefix)
            if invoked_prefix is None:
                return

        trigger = view.get_word()

        command = Command.objects.filter(trigger=trigger)

        if command.count() != 0:
            command = command.first()

            if command.file:
                await self.bot.send_file(message.channel, command.file.path, content=None)
            else:
                await self.bot.send_message(message.channel, content=command.response)

def setup(bot):
    bot.add_cog(Responder(bot))
