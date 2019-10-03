from discord.ext.commands import (
    Cog,
    is_owner,
    NoPrivateMessage,
    BadArgument,
    MissingPermissions,
)
from discord.ext import commands
from discord import TextChannel, DMChannel
from dangobot.core.helpers import guild_fetch_or_create


class Admin(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(hidden=True)
    @is_owner()
    async def debug(self, ctx):
        pass

    @debug.command()
    async def resetguild(self, ctx):
        await guild_fetch_or_create(self.bot.db_pool, ctx.guild)
        await ctx.send(content=f"Reset guild {ctx.guild.name}")

    @commands.command(hidden=True, rest_as_raw=False)
    async def say(self, ctx, channel: TextChannel, *, message):
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
    async def say_errors(self, ctx, error):
        if isinstance(error, NoPrivateMessage) or isinstance(
            error, BadArgument
        ):
            await ctx.send(content=error)


def setup(bot):
    bot.add_cog(Admin(bot))
