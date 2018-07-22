from .models import Command

from asyncpg import exceptions
from discord import File
from discord.ext import commands
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
        if not ctx.guild:  # we don't want commands to work in DMs
            return

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

    @commands.group(name='commands', invoke_without_command=True)
    async def cmds(self, ctx):
        """
        Management of user-defined commands.
        """
        await ctx.send_help('commands')

    @cmds.command()
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, trigger: str, *, response: str):
        """
        Add a new command.
        """
        async with self.bot.db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO {table}(guild_id, trigger, response, file) "
                "VALUES ($1, $2, $3, '')".format(table=self.table),
                ctx.guild.id, trigger, response
            )

        await ctx.send('Command `{}` added successfully!'.format(trigger))

    @add.error
    async def add_error(self, ctx, error):
        if (
            isinstance(error, commands.CommandInvokeError) and
            isinstance(error.original, exceptions.UniqueViolationError)
        ):
            await ctx.send(
                'Command `{}` already exists!'.format(ctx.args[-1])
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                'You need to specify the {}!'.format(error.param.name)
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
                ctx.guild.id
            )

        list = '\n'.join(
            map(lambda c: '  {}{}'.format(ctx.prefix, c['trigger']), commands)
        )
        list = '```Defined commands:\n{}```'.format(list)

        await ctx.send(content=list)

    @cmds.command()
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx):
        pass

    @cmds.command()
    @commands.has_permissions(administrator=True)
    async def edit(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Commands(bot))
