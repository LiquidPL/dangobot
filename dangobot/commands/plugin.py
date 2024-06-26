import logging
import os

from aiohttp import ClientError, ClientResponseError
from asyncpg import exceptions
from discord import File, Embed
from discord.ext import commands
from discord.ext.commands import (
    BadArgument,
    NoPrivateMessage,
    CommandError,
    Context,
)
from django.conf import settings

import validators

from dangobot.core.bot import command_handler, DangoBot
from dangobot.core.plugin import Cog
from dangobot.core.helpers import download_file, FileTooLarge

from .models import file_path
from .data import ParsedCommand
from .repository import CommandRepository


logger = logging.getLogger(__name__)


class Commands(Cog):
    """A plugin for configuring custom user-made bot commands."""

    @command_handler
    async def handle_command(self, ctx: Context) -> bool:
        """
        The command handler.

        Handles all incoming command invocations, and checks if there's
        a custom command defined with the given name. If it exists, its
        contents are pulled from the database, and sent to the target channel.

        Arguments:
            message (string): the incoming message
        """
        if not ctx.guild:  # we don't want commands to work in DMs
            return False

        if not ctx.invoked_with:
            return False

        command = await CommandRepository().find_by_trigger(
            ctx.invoked_with, ctx.guild
        )

        if command:
            await self.send_response(ctx, command)
            return True

        return False

    async def send_response(self, ctx: Context, command) -> None:
        """Sends a response for a given custom command database record."""
        params = {"content": command["response"]}

        if command["file"] == "":
            await ctx.send(**params)
        else:
            # TODO: actual asynchronous file read
            with open(
                os.path.join(settings.MEDIA_ROOT, command["file"]), "rb"
            ) as file:
                params["file"] = File(file, command["original_file_name"])
                await ctx.send(**params)

    async def parse_command(self, ctx: Context, args) -> ParsedCommand:
        """
        Parse the command syntax used for the :func:`add` and :func:`edit`
        functions.

        The format of the command is as follows:
        * the first word is the command trigger,
        * rest of the string is treated as the command response, until the last
          word starts with ``attachment=``,
        * if so, then the last word specifies a file attachment that will be a
          part of the command.

        The attachment is provided as an ``attachment=<url>`` parameter at the
        end of the command. The file under the URL is then downloaded and saved
        in the media location.

        This means that the command response can have a length of zero if you
        only specify the trigger and the attachment.

        Keep in mind that if there is an attachment provided as a part of the
        message (as in: uploaded in Discord, not as as an URL posted in the
        message body), then it will take precedence over the attachment posted
        in the command.

        Returns a four-element tuple where:
        * the first element is a command trigger,
        * the second element is the command response,
        * the third element is a path to an eventual attachment (relative to
          the media directory), if there's no attachment then it is an empty
          string,
        * the fourth element is the orignal file name of the attachment, or
          an empty string if there's no attachment.
        """
        if len(args) < 2 and len(ctx.message.attachments) < 1:
            raise BadArgument("No message content specified!")

        url = ""
        path_relative = ""
        filename = ""

        if args[-1].startswith("attachment="):
            url = args[-1].replace("attachment=", "", 1)

            if not validators.url(url):
                raise commands.BadArgument(
                    message="The provided URL is incorrect!"
                )

            args = args[:-1]

        if len(ctx.message.attachments) > 0:
            url = ctx.message.attachments[0].url

        if url != "":
            filename = url.split("/")[-1]
            # relative path is being saved to the database
            path_relative = file_path(ctx, filename)
            path_absolute = f"{settings.MEDIA_ROOT}/{path_relative}"

            try:
                await download_file(self.bot.http_session, url, path_absolute)
            except ClientError as exc:
                if isinstance(exc, ClientResponseError) and exc.status == 404:
                    raise CommandError(
                        "The requested file was not found!"
                    ) from exc

                logger.error(
                    "An error occured while downloading file %s to %s.",
                    url,
                    path_absolute,
                    exc_info=True,
                )

                raise exc
            except FileTooLarge as exc:
                raise CommandError(str(exc)) from exc

        trigger = args[0]
        response = " ".join(args[1:])

        return ParsedCommand(trigger, response, path_relative, filename)

    @commands.group(name="commands", invoke_without_command=True)
    async def cmds(self, ctx):
        """
        Management of user-defined commands.
        """
        await ctx.send_help("commands")

    @cmds.command(usage="<trigger> (<response>) (attachment=url)")
    @commands.has_permissions(administrator=True)
    async def add(self, ctx: Context, *args):
        """
        Add a new command.

        Parameters:

          * trigger: the string that will trigger executing this command.
          * response: the string that will be sent by this command.\
            Can be empty.
          * url: URL to a file that will be sent by this command.\
            Can be omitted.

        Executing the command without specifying either RESPONSE or ATTACHMENT
        will result in an error. You can also upload an attachment to Discord
        instead of specifying the URL.
        """
        if ctx.guild is None:
            raise NoPrivateMessage("This command cannot be used in a DM")

        command = await self.parse_command(ctx, *args)

        try:
            await CommandRepository().add_to_guild(ctx.guild, command)
        except exceptions.UniqueViolationError as exc:
            raise BadArgument(
                f"Command `{ctx.args[-1]}` already exists!"
            ) from exc

        await ctx.send(f"Command `{command.trigger}` added successfully!")

    @cmds.command()
    async def list(self, ctx: Context):
        """
        List all commands defined in the server.
        """
        if ctx.guild is None:
            raise NoPrivateMessage("This command cannot be used in a DM")

        command_list = await CommandRepository().find_all_from_guild(ctx.guild)

        embed = Embed()
        embed.title = "Available custom commands:"
        embed.description = "\n".join(
            map(
                lambda c: f"{ctx.prefix}{c['trigger']}",
                command_list,
            )
        )

        await ctx.send(embed=embed)

    @cmds.command()
    @commands.has_permissions(administrator=True)
    async def delete(self, ctx: Context, trigger: str):
        """
        Deletes a command from the server.
        """
        if ctx.guild is None:
            raise NoPrivateMessage("This command cannot be used in a DM")

        deleted = await CommandRepository().delete_from_guild(
            trigger, ctx.guild
        )

        if deleted:
            message = "Command `{}` deleted successfully!"
        else:
            message = "Command `{}` does not exist!"

        await ctx.send(content=message.format(trigger))

    @cmds.command(usage="<trigger> (<response>) (attachment=url)")
    @commands.has_permissions(administrator=True)
    async def edit(self, ctx: Context, *args):
        """
        Edit an existing command.

        Has the same parameters as the add command.
        """
        if ctx.guild is None:
            raise NoPrivateMessage("This command cannot be used in a DM")

        command = await self.parse_command(ctx, *args)

        updated = await CommandRepository().update_in_guild(ctx.guild, command)

        if updated:
            message = "Command `{}` updated successfully!"
        else:
            message = "Command `{}` does not exist!"

        await ctx.send(content=message.format(command.trigger))


async def setup(bot: DangoBot):  # pylint: disable=missing-function-docstring
    await bot.add_cog(Commands(bot))
