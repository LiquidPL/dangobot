from discord.ext import commands
from discord.ext.commands import (
    Context,
    NoPrivateMessage,
    BadArgument,
    MissingPermissions,
)
from discord import User, TextChannel, VoiceChannel
from discord.abc import PrivateChannel

from dangobot.core.bot import DangoBot
from dangobot.core.plugin import Cog


_GuildMessageable = TextChannel | VoiceChannel


class Admin(Cog):
    """
    Contains commands useful to server (and bot) administrators.
    """

    @commands.command(hidden=True, rest_as_raw=False)
    async def say(self, ctx: Context, channel: _GuildMessageable, *, message):
        """
        Sends a message in any channel in this server that the bot has access\
        to.

        Available only to server administrators.
        """
        if isinstance(
            ctx.channel, PrivateChannel
        ) and not await self.bot.is_owner(ctx.author):
            raise NoPrivateMessage(
                message="You can't use this command in a DM!"
            )

        if ctx.guild is None or ctx.guild.id != channel.guild.id:
            raise BadArgument(
                message="You can't send messages outside of your server!"
            )

        if isinstance(ctx.author, User):
            return

        if not ctx.channel.permissions_for(ctx.author).administrator:
            raise MissingPermissions(["administrator"])

        await channel.send(content=message)
        await ctx.send(content="Message sent!")


async def setup(bot: DangoBot):  # pylint: disable=missing-function-docstring
    await bot.add_cog(Admin(bot))
