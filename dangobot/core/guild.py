from dataclasses import dataclass
from functools import wraps
from typing import Optional

from django.conf import settings

from discord import Guild

from .repository import GuildRepository


def _ensure_guild(func):
    """
    An annotation that ensures that the `guild` argument of the annotated
    function is of the :class:`~discord.Guild` type.
    """

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
    """
    A class serving as an in-memory cache for important guild configuration.
    """

    # TODO: refactor this into a repository
    def __init__(self):
        self.guilds = {}

    @_ensure_guild
    async def get_prefix(self, guild=None):
        """Gets the command prefix for a given guild."""
        if self.guilds[guild.id].prefix is None:
            # putting this in cache to avoid a race condition where
            # the prefix would be retrieved a second time before
            # the first retrieve would put it in the database
            self.guilds[guild.id].prefix = settings.COMMAND_PREFIX
            await GuildRepository().create_from_gateway_response(guild)

        return self.guilds[guild.id].prefix

    @_ensure_guild
    async def set_prefix(self, prefix, guild=None):
        """Sets a new command prefix for a given guild."""
        if prefix == self.guilds[guild.id].prefix:
            return False

        updated = await GuildRepository().update_command_prefix(guild, prefix)

        if updated:
            self.guilds[guild.id].prefix = prefix
            return True


@dataclass
class _Guild:
    id: int  # pylint: disable=invalid-name
    prefix: Optional[str] = None
