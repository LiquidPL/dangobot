from discord.ext.commands import (
    Context,
    is_owner,
    NoPrivateMessage,
    BadArgument,
    MissingPermissions,
)
from discord.ext import commands
from discord import TextChannel, DMChannel

from dangobot.core.plugin import Cog
from dangobot.core.repository import GuildRepository


class Admin(Cog):
    """
    Contains commands useful to server (and bot) administrators.
    """

    @commands.group(hidden=True)
    @is_owner()
    async def debug(self, ctx):
        """
        Various commands uses for debugging, available only for the bot owner.
        """

    @debug.command()
    async def resetguild(self, ctx: Context):
        """
        Forces the bot to fetch a guild from the gateway and create an entry\
        for it in the database.

        If there already exists an entry for the guild in the database,\
        it **will** be destroyed. This will usually result in loss of all\
        the guild related information from the database.
        """
        await GuildRepository().destroy_by_id(ctx.guild.id)
        await GuildRepository().create_from_gateway_response(ctx.guild)
        await ctx.send(content=f"Reset guild {ctx.guild.name}")

    @commands.command(hidden=True, rest_as_raw=False)
    async def say(self, ctx: Context, channel: TextChannel, *, message):
        """
        Sends a message in any channel in this server that the bot has access\
        to. Available only to server administrators.
        """
        if isinstance(ctx.channel, DMChannel):
            if not await self.bot.is_owner(ctx.author):
                raise NoPrivateMessage(
                    message="You can't use this command in a DM!"
                )

        if isinstance(ctx.channel, TextChannel):
            if ctx.guild.id != channel.guild.id:
                raise BadArgument(
                    message="You can't send messages outside of your server!"
                )

            if not ctx.channel.permissions_for(ctx.author).administrator:
                raise MissingPermissions(["administrator"])

        await channel.send(content=message)

    @say.error
    async def say_errors(
        self, ctx, error
    ):  # pylint: disable=missing-function-docstring
        if isinstance(error, (BadArgument, NoPrivateMessage)):
            await ctx.send(content=error)


def setup(bot):  # pylint: disable=missing-function-docstring
    bot.add_cog(Admin(bot))
