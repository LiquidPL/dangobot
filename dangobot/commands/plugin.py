from .models import Command, file_path

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

async def random_name():
    yield ''.join([random.choice(
        '{}{}'.format(string.ascii_letters, string.digits)
    ) for i in range(8)])

async def save_file(url, path):
    [directory, filename] = path.rsplit('/', 1)

    while os.path.exists(path):
        path = '{}/{}_{}'.format(directory, await random_name(), filename)

    absolute_path = os.path.join(settings.MEDIA_ROOT, path)

    logger.info(absolute_path)

    file = open(absolute_path, 'wb')

    async with self.bot.http_session.get(file_url) as r:
        while True:
            chunk = await r.content.read(1024)
            if not chunk:
                break

            file.write(chunk)

    # yield file


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

    async def save_command(self, ctx, trigger, response, file_url=None):
        if file_url:
            filename = file_url.split('/')[-1]
            file = await save_file(file_url, file_path(ctx, filename))

            path = file.name
        else:
            path = ''

        async with self.bot.db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO {table}(guild_id, trigger, response, file) "
                "VALUES ($1, $2, $3, $4)".format(table=self.table),
                ctx.guild.id, trigger, response, path
            )

    @commands.group(name='commands', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def cmds(self, ctx):
        """
        Management of user-defined commands.
        """
        await ctx.send_help('commands')

    @cmds.error
    async def cmds_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permissions to do this!")

    @cmds.command()
    async def add(self, ctx, trigger: str, *, response: str):
        """
        Add a new command.
        """
        url = (None if not ctx.message.attachments
               else ctx.message.attachments[0].url)

        await self.save_command(ctx, trigger, response, file_url=url)
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
        else:
            await ctx.send('An error has occured!')
            logger.exception(error)

    async def addimage(self, ctx, trigger: str, url: str, *, response: str):
        pass

    @cmds.command()
    async def uploadtest(self, ctx):
        await ctx.send(ctx.message.attachments[0].url)
        await ctx.send(ctx.message.attachments[0].proxy_url)

    @cmds.command()
    async def remove(self, ctx):
        pass

    @cmds.command()
    async def edit(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Commands(bot))
