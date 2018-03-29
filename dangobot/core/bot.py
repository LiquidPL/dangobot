from discord.ext import commands
from django.conf import settings
from django.db import connection

import asyncpg
import logging

logger = logging.getLogger(__name__)


class DangoBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=settings.COMMAND_PREFIX,
            description=settings.DESCRIPTION
        )

    async def on_ready(self):
        self.pool = await asyncpg.create_pool(
            database=connection.settings_dict['NAME'],
            user=connection.settings_dict['USER'],
            password=connection.settings_dict['PASSWORD'],
            host=connection.settings_dict['HOST'],
            port=connection.settings_dict['PORT']
        )

        logger.info('Logged in as {0}'.format(self.user))

    async def on_guild_join(self, guild):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM core_guild WHERE id = $1',
                guild.id
            )

            if row is None:
                await conn.execute(
                    'INSERT INTO core_guild(id, name) VALUES ($1, $2)',
                    guild.id, guild.name
                )
