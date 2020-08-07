from .helpers import guild_fetch_or_create
from .models import Guild as DBGuild

from django.conf import settings

from dataclasses import dataclass
from functools import wraps

from discord import Guild


def _ensure_guild(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        if "guild" not in kwargs:
            raise TypeError("missing keyword argument: 'guild'")

        guild = kwargs["guild"]

        if not isinstance(guild, Guild):
            raise ValueError("This argument requires a discord guild")

        if guild.id not in self.guilds:
            self.guilds[guild.id] = _Guild(id)

        return await func(self, *args, **kwargs)
    return wrapper


class GuildCache:
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self.guilds = {}

    @_ensure_guild
    async def get_prefix(self, guild=None):
        if self.guilds[guild.id].prefix is None:
            # putting this in cache to avoid a race condition where
            # the prefix would be retrieved a second time before
            # the first retrieve would put it in the database
            self.guilds[guild.id].prefix = settings.COMMAND_PREFIX
            await guild_fetch_or_create(self.db_pool, guild)

        return self.guilds[guild.id].prefix

    @_ensure_guild
    async def set_prefix(self, prefix, guild=None):
        if prefix == self.guilds[guild.id].prefix:
            return False

        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                f"UPDATE {DBGuild._meta.db_table} "
                "SET command_prefix = $1 "
                "WHERE id = $2",
                prefix,
                guild.id,
            )

        if int(result.split()[1]) == 1:
            self.guilds[guild.id].prefix = prefix
            return True


@dataclass
class _Guild:
    id: int
    prefix: str = None
