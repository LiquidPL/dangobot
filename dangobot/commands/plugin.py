from .models import Command, file_path

from dangobot.core.helpers import download_file
from dangobot.core.errors import DownloadError

from asyncpg import exceptions
from discord import File
from discord.ext import commands
from discord.ext.commands import Cog, BadArgument
from django.conf import settings

import logging
import os
import validators

logger = logging.getLogger(__name__)


class Commands(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.table = Command._meta.db_table

    @Cog.listener()
    async def on_message(self, message):
        await self.process_messages(message)

    async def process_messages(self, message):
        ctx = await self.bot.get_context(message)
        if not ctx.guild:  # we don't want commands to work in DMs
            return

        trigger = ctx.invoked_with

        async with self.bot.db_pool.acquire() as conn:
            command = await conn.fetchrow(
                "SELECT * FROM {table} "
                "WHERE guild_id = $1 "
                "AND trigger = $2".format(table=self.table),
                ctx.guild.id,
                trigger,
            )

        if command:
            params = {"content": command["response"]}

            if command["file"] != "":
                # TODO actual asynchronous file read
                params["file"] = File(
                    open(
                        os.path.join(settings.MEDIA_ROOT, command["file"]),
                        "rb",
                    ),
                    command["original_file_name"],
                )

            await ctx.send(**params)

    async def parse_command(self, ctx, *args):
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

        Returns a three-element list where:
        * the first element is a command trigger,
        * the second element is the command response,
        * the third element is a path to an eventual attachment (relative to
          the media directory), if there's no attachment then it is an empty
          string,
        * the fourth element is the orignal file name of the attachment.
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

            await download_file(self.bot.http_session, url, path_absolute)

        trigger = args[0]
        response = " ".join(args[1:])

        return [trigger, response, path_relative, filename]

    @commands.group(name="commands", invoke_without_command=True)
    async def cmds(self, ctx):
        """
        Management of user-defined commands.
        """
        await ctx.send_help("commands")

    @cmds.command(usage="<trigger> (<response>) (attachment=url)")
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, *args):
        """
        Add a new command.

        Parameters:
          * trigger: the string that will trigger executing this command.
          * response: the string that will be sent by this command. Can be empty.
          * url: URL to a file that will be sent by this command. Can be omitted.

        Executing the command without specifying either RESPONSE or ATTACHMENT will result in an error. You can also upload an attachment to Discord instead of specifying the URL.
        """
        try:
            params = await self.parse_command(ctx, *args)
        except (BadArgument, DownloadError) as e:
            await ctx.send(content=e)
            return

        async with self.bot.db_pool.acquire() as conn:
            try:
                await conn.execute(
                    "INSERT INTO {table}"
                    "(guild_id, trigger, response, file, original_file_name) "
                    "VALUES ($1, $2, $3, $4, $5)".format(table=self.table),
                    ctx.guild.id,
                    *params,
                )
            except exceptions.UniqueViolationError:
                await ctx.send(
                    "Command `{}` already exists!".format(ctx.args[-1])
                )
                return

        await ctx.send("Command `{}` added successfully!".format(params[0]))

    @add.error
    async def add_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "You need to specify the {}!".format(error.param.name)
            )

    @cmds.command()
    async def list(self, ctx):
        """
        List all commands defined in the server.
        """
        async with self.bot.db_pool.acquire() as conn:
            commands = await conn.fetch(
                "SELECT trigger FROM {table} "
                "WHERE guild_id = $1".format(table=self.table),
                ctx.guild.id,
            )

        list = "\n".join(
            map(lambda c: "  {}{}".format(ctx.prefix, c["trigger"]), commands)
        )
        list = "```Defined commands:\n{}```".format(list)

        await ctx.send(content=list)

    @cmds.command()
    @commands.has_permissions(administrator=True)
    async def delete(self, ctx, trigger: str):
        """
        Deletes a command from the server.
        """
        async with self.bot.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM {table} "
                "WHERE guild_id = $1 "
                "and trigger = $2".format(table=self.table),
                ctx.guild.id,
                trigger,
            )

        # the return value of a DELETE psql statement is
        # 'DELETE <number of deleted rows>'
        if int(result.split(" ")[1]) == 0:
            message = "Command `{}` does not exist!"
        else:
            message = "Command `{}` deleted successfully!"

        await ctx.send(content=message.format(trigger))

    @delete.error
    async def delete_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "You need to specify the {}!".format(error.param.name)
            )

    @cmds.command(usage="<trigger> (<response>) (attachment=url)")
    @commands.has_permissions(administrator=True)
    async def edit(self, ctx, *args):
        """
        Edit an existing command.

        Shares syntax with the add command.
        """
        try:
            params = await self.parse_command(ctx, *args)
        except (BadArgument, DownloadError) as e:
            await ctx.send(content=e)
            return

        async with self.bot.db_pool.acquire() as conn:
            result = await conn.execute(
                f"UPDATE {self.table} "
                "SET response = $3, file = $4, original_file_name = $5"
                "WHERE guild_id = $1 AND trigger = $2",
                ctx.guild.id,
                *params,
            )

        if int(result.split(" ")[1] == 0):
            message = "Command `{}` does not exist!"
        else:
            message = "Command `{}` updated successfully!"

        await ctx.send(content=message.format(params[0]))


def setup(bot):
    bot.add_cog(Commands(bot))
