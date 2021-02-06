from discord.ext.commands import (
    Cog,
    is_owner,
    NoPrivateMessage,
    BadArgument,
    MissingPermissions,
)
from discord.ext import commands
from discord import TextChannel, DMChannel
from discord.ext.commands.core import has_permissions
from dangobot.core.helpers import guild_fetch_or_create


class Admin(Cog):
    """
    Contains commands useful to server (and bot) administrators.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.group(hidden=True)
    @is_owner()
    async def debug(self, ctx):
        """
        Various commands uses for debugging, available only for the bot owner.
        """

    @debug.command()
    async def resetguild(self, ctx):
        """
        Forces the bot to fetch a guild from the gateway and create an entry\
        for it in the database.
        """
        await guild_fetch_or_create(self.bot.db_pool, ctx.guild)
        await ctx.send(content=f"Reset guild {ctx.guild.name}")

    @commands.command(hidden=True, rest_as_raw=False)
    @has_permissions(administrator=True)
    async def say(self, ctx, channel: TextChannel, *, message):
        """
        Sends a message in any channel in this server that the bot has access\
        to. Available only to server administrators.
        """
        if isinstance(ctx.channel, DMChannel) and not self.bot.is_owner(
            ctx.author
        ):
            raise NoPrivateMessage(
                message="You can't use this command in a DM!"
            )

        if ctx.guild.id != channel.guild.id:
            raise BadArgument(
                message="You can't send messages outside of your server!"
            )

        if not ctx.channel.permissions_for(ctx.author).administrator:
            raise MissingPermissions(["administrator"])

        await channel.send(content=message)

    @say.error
    async def say_errors(self, ctx, error):  # pylint: disable=missing-function-docstring
        if isinstance(error, (BadArgument, NoPrivateMessage)):
            await ctx.send(content=error)


def setup(bot):  # pylint: disable=missing-function-docstring
    bot.add_cog(Admin(bot))
