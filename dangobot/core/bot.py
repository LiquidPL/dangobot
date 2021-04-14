import importlib
import logging
import traceback

from discord import Embed
from discord.ext.commands.context import Context
from discord.guild import Guild
from discord.ext import commands
from django.conf import settings

import aiohttp

from dangobot import loop

from .help import DangoHelpCommand
from .repository import GuildRepository


logger = logging.getLogger(__name__)


class DangoBot(commands.Bot):
    """The core bot class."""

    def __init__(self):
        super().__init__(
            loop=loop,
            command_prefix=self.get_command_prefix,
            description=settings.DESCRIPTION,
            help_command=DangoHelpCommand(),
        )

        self.http_session = None

        for app in settings.INSTALLED_APPS:
            try:
                spec = importlib.util.find_spec(f"{app}.plugin")

                if spec:
                    logger.info("Loading extension %s", app)
                    self.load_extension(f"{app}.plugin")

            except Exception:  # pylint: disable=broad-except
                logger.exception("Failed to load extension %s", app)

    async def get_command_prefix(
        self, bot, message
    ):  # pylint: disable=unused-argument
        """
        Gets the command prefix used by the guild that this message
        originated from.
        """
        if message.guild is None:
            return settings.COMMAND_PREFIX

        return await GuildRepository().get_command_prefix(guild=message.guild)

    async def on_ready(self):  # pylint: disable=missing-function-docstring
        self.http_session = aiohttp.ClientSession()

        logger.info("Logged in as %s", self.user)

    async def on_guild_join(
        self, guild
    ):  # pylint: disable=missing-function-docstring
        await GuildRepository().create_from_gateway_response(guild)

    async def on_guild_update(
        self, before: Guild, after: Guild
    ):  # pylint: disable=missing-function-docstring:
        if before.name == after.name:
            return  # we're only tracking guild names for now

        guild = await GuildRepository().find_by_id(after.id)

        if guild:
            await GuildRepository().update_from_gateway_response(after)
        else:
            await GuildRepository().create_from_gateway_response(after)

    async def on_command_error(self, context: Context, exception):
        if isinstance(exception, commands.CommandInvokeError):
            await context.send(
                content="Sorry, an error has occured! "
                "The bot owner has been informed of this."
            )

            exc = exception.original
            logger.error("%s: %s", exc.__class__.__name__, exc)

            if settings.SEND_ERRORS:
                if not hasattr(settings, "OWNER_ID") or not settings.OWNER_ID:
                    logger.error(
                        "You haven't set the owner's user ID in the "
                        "settings file. Aborting."
                    )
                    return

                owner = await self.fetch_user(settings.OWNER_ID)
                dm_channel = owner.dm_channel or await owner.create_dm()

                embed = await self.format_traceback(exc)

                await dm_channel.send(embed=embed)
        elif isinstance(exception, commands.MissingPermissions):
            await context.send(
                content="You don't have the permissions to do this!"
            )
        elif isinstance(exception, commands.MissingRequiredArgument):
            await context.send(
                "You need to specify `{}`!".format(exception.param.name)
            )
            await context.send_help(context.command.qualified_name)

    async def format_traceback(self, exception):
        """
        Format a traceback ready to be posted as a
        Discord embed given an exception.
        """
        trace = traceback.format_exception(
            exception.__class__, exception, exception.__traceback__
        )
        trace_orig = "".join(trace)

        length = len(trace_orig)

        # remove oldest traces until we're under the embed length cap,
        # which is 1000, minus 6 characters for codeblock start and end,
        # 4 for a 3 character ellipsis (...) and a newline character
        while length > 990:
            element_length = len(trace[1])
            del trace[1]
            length -= element_length

        if len(trace_orig) > 990:
            trace.insert(1, "...\n")

        trace = "".join(trace)

        # upload full, unedited traceback to a pastebin
        async with self.http_session.post(
            "http://dpaste.com/api/v2/",
            data={"expiry_days": 21, "syntax": "pytb", "content": trace_orig},
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
