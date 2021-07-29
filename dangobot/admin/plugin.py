from discord.ext.commands import (
    Context,
    NoPrivateMessage,
    BadArgument,
    MissingPermissions,
)
from discord.ext import commands
from discord import TextChannel, DMChannel

from dangobot.core.plugin import Cog


class Admin(Cog):
    """
    Contains commands useful to server (and bot) administrators.
    """

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


def setup(bot):  # pylint: disable=missing-function-docstring
    bot.add_cog(Admin(bot))
