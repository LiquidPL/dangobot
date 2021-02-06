from discord.ext.commands import Cog, has_permissions
from discord.ext import commands


class Management(Cog):
    """Configuration of the bot."""
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def config(self, ctx):  # pylint: disable=missing-function-docstring
        await ctx.send_help("config")

    @config.command()
    @has_permissions(administrator=True)
    async def setprefix(self, ctx, prefix: str):
        """Sets a new command prefix for the bot commands."""
        if await self.bot.cache.set_prefix(prefix, guild=ctx.guild):
            message = f"Command prefix changed to `{prefix}`."
        else:
            message = f"`{prefix}` is already your prefix."

        await ctx.send(content=message)


def setup(bot):  # pylint: disable=missing-function-docstring
    bot.add_cog(Management(bot))
