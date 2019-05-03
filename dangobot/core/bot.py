from discord import Embed
from discord.ext import commands
from django.conf import settings
from django.db import connection

from .helpers import guild_fetch_or_create
from .help import DangoHelpCommand

import aiohttp
import asyncpg
import importlib
import logging
import traceback

logger = logging.getLogger(__name__)


class DangoBot(commands.Bot):
    def __init__(self):
        self.prefixes = {}

        super().__init__(
            command_prefix=self.command_prefix,
            description=settings.DESCRIPTION,
            help_command=DangoHelpCommand()
        )

        for app in settings.INSTALLED_APPS:
            try:
                spec = importlib.util.find_spec(f"{app}.plugin")

                if spec:
                    logger.info(f"Loading extension {app}")
                    self.load_extension(f"{app}.plugin")

            except Exception:
                logger.exception(f"Failed to load extension {app}")

    async def command_prefix(self, bot, message):
        if message.guild is None:
            return settings.COMMAND_PREFIX

        if message.guild.id not in self.prefixes:
            guild = await guild_fetch_or_create(self.db_pool, message.guild)

            self.prefixes[message.guild.id] = guild["command_prefix"]

        return self.prefixes[message.guild.id]

    async def on_ready(self):
        self.db_pool = await asyncpg.create_pool(
            database=connection.settings_dict["NAME"],
            user=connection.settings_dict["USER"],
            password=connection.settings_dict["PASSWORD"],
            host=connection.settings_dict["HOST"],
            port=connection.settings_dict["PORT"],
        )

        self.http_session = aiohttp.ClientSession()

        logger.info("Logged in as {0}".format(self.user))

    async def on_guild_join(self, guild):
        await guild_fetch_or_create(self.db_pool, guild)

    async def on_guild_update(self, before, after):
        if before.name == after.name:
            return  # we're only tracking guild names for now

        row = await guild_fetch_or_create(self.db_pool, after)

        if row:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE core_guild SET name = $1 WHERE id = $2",
                    after.name,
                    after.id,
                )

    async def on_command_error(self, context, exception):
        if isinstance(exception, commands.CommandInvokeError):
            await context.send(
                content="Sorry, an error has occured! "
                "The bot owner has been informed of this."
            )

            e = exception.original
            logger.error("{}: {}".format(e.__class__.__name__, e))

            if settings.SEND_ERRORS:
                if not hasattr(settings, "OWNER_ID") or not settings.OWNER_ID:
                    logger.error(
                        "You haven't set the owner's user ID in the "
                        "settings file. Aborting."
                    )
                    return

                owner = await self.fetch_user(settings.OWNER_ID)
                dm = owner.dm_channel or await owner.create_dm()

                embed = await self.format_traceback(e)

                await dm.send(embed=embed)
        elif isinstance(exception, commands.MissingPermissions):
            await context.send(
                content="You don't have the permissions to do this!"
            )

    async def format_traceback(self, exception):
        """
        Format a traceback ready to be posted as a
        Discord embed given an exception.
        """
        trace = traceback.format_exception(
            exception.__class__, exception, exception.__traceback__
        )
        trace_orig = "".join(trace)

        length = sum(len(el) for el in trace)

        # remove oldest traces until we're under the embed
        # length cap, which is1000, minus 6 characters for
        # codeblock start and end, 4 for a 3 character
        # ellipsis (...) and a newline character
        while length > 990:
            element_length = len(trace[1])
            del trace[1]
            length = length - element_length

        trace.insert(1, "...\n")
        trace = "".join(trace)

        # upload full, unedited traceback to a pastebin
        async with self.http_session.post(
            "http://dpaste.com/api/v2/",
            data={"expiry_days": 21, "syntax": "py3tb", "content": trace_orig},
        ) as resp:
            trace_url = await resp.text()

        return (
            Embed(title="❌ An error has occured!", color=0xff0000)
            .add_field(
                name=exception.__class__.__module__
                + "."
                + exception.__class__.__qualname__,
                value="```{}```".format(trace),
                inline=False,
            )
            .add_field(name="Full traceback:", value=trace_url)
        )
