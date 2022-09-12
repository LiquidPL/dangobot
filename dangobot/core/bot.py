import importlib
import inspect
import logging
import traceback
from typing import Callable, Coroutine, List, Optional, Tuple

from discord.ext.commands import Context, errors
from discord.guild import Guild
from discord.ext import commands
from django.conf import settings

import aiohttp

from dangobot import loop
from dangobot.core.embeds import ErrorEmbedFormatter

from .help import DangoHelpCommand
from .repository import GuildRepository
from .plugin import Cog


logger = logging.getLogger(__name__)


def command_handler(
    meth: Callable[[Cog, Context], Coroutine[None, None, bool]]
) -> Callable[[Cog, Context], Coroutine[None, None, bool]]:
    """
    Registers this coroutine as a command handler for the bot.

    This function will be called whenever the bot detects a command has been
    invoked in a message, before calling the native command handling code.

    It should have only one argument, the :class:`discord.ext.commands.Context`
    for the invoked command, and return a `bool`, signalling whether it has
    handled this invocation, or ignored it.
    """
    if inspect.iscoroutinefunction(meth) is False:
        raise TypeError(f"{meth.__qualname__} is not a coroutine")

    annotations = getattr(meth, "__annotations__", None)

    if isinstance(annotations, dict):
        annotations["command_handler"] = True

    return meth


class DangoBot(commands.Bot):
    """The core bot class."""

    _command_handlers: List[Tuple[str, str]] = []

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

        for name, cog in self.cogs.items():
            self.register_command_handlers(name, cog)

    def register_command_handlers(self, cog_name: str, cog: Cog):
        """
        Finds all methods decorated with :func:`command_handler` in the
        specified `cog`, and registers them with the bot as command handlers.

        Parameters
        ----------
        cog_name: `str`
            Name of the cog.

        cog: :class:`dangobot.core.plugin.Cog`
            The actual cog class.
        """
        for _, method in inspect.getmembers(cog, inspect.iscoroutinefunction):
            annotations: Optional[dict]
            annotations = getattr(method, "__annotations__", None)

            if annotations is None:
                continue

            if annotations.get("command_handler", False) is True:
                self._command_handlers.append((cog_name, method.__name__))

    # async def post_what_can_i_say_except_delete_this_when_rafal_posts_cringe(
    #     self, ctx: Context
    # ) -> None:
    #     pass

    async def execute_command_handlers(self, ctx: Context) -> bool:
        """
        Executes all registered command handlers for a given context.

        Parameters
        ----------
        ctx: :class:`discord.ext.commands.Context`
            The command invocation context.
        """
        command_handled = False

        for cog_name, method_name in self._command_handlers:
            cog = self.get_cog(cog_name)

            if cog is None:
                continue

            method = getattr(cog, method_name, None)

            if method is None:
                continue

            command_handled = await method(ctx)

        return command_handled

    async def invoke(self, ctx):
        handled_by_custom_handler = await self.execute_command_handlers(ctx)

        if ctx.command is not None:
            self.dispatch("command", ctx)
            try:
                if await self.can_run(ctx, call_once=True):
                    await ctx.command.invoke(ctx)
                else:
                    raise errors.CheckFailure(
                        "The global check once functions failed."
                    )
            except errors.CommandError as exc:
                await ctx.command.dispatch_error(ctx, exc)
            else:
                self.dispatch("command_completion", ctx)
        elif ctx.invoked_with and handled_by_custom_handler is False:
            error = errors.CommandNotFound(
                f'Command "{ctx.invoked_with}" is not found'
            )
            self.dispatch("command_error", ctx, error)

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
                embed=ErrorEmbedFormatter().format(
                    title="Sorry, an error has occurred!",
                    description="The bot owner has been informed about this.",
                )
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
                f"You need to specify `{exception.param.name}`!"
            )
            await context.send_help(context.command.qualified_name)
        elif isinstance(exception, commands.CommandError):
            await context.send(
                embed=ErrorEmbedFormatter().format(description=exception)
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
            ErrorEmbedFormatter()
            .format(title="An error has occured!")
            .add_field(
                name=exception.__class__.__module__
                + "."
                + exception.__class__.__qualname__,
                value=f"```{trace}```",
                inline=False,
            )
            .add_field(name="Full traceback:", value=trace_url)
        )
