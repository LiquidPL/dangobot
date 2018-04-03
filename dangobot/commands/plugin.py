from .models import Command

from discord import File
from django.conf import settings

import logging
import os

logger = logging.getLogger(__name__)


def open_file(path):
    if not path:
        return None

    return File(open(
        os.path.join(settings.MEDIA_ROOT, path),
        'rb'
    ))


class Commands:
    def __init__(self, bot):
        self.bot = bot
        self.table = Command._meta.db_table

    async def on_message(self, message):
        ctx = await self.bot.get_context(message)
        trigger = ctx.invoked_with

        async with self.bot.db_pool.acquire() as conn:
            command = await conn.fetchrow(
                'SELECT * FROM {table} WHERE guild_id = $1 AND trigger = $2'
                .format(table=self.table),
                ctx.guild.id, trigger
            )

            if command:
                await ctx.send(
                    content=command['response'],
                    file=open_file(command['file'])
                )


def setup(bot):
    bot.add_cog(Commands(bot))
