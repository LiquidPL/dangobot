from discord.ext.commands import Cog, has_permissions
from discord.ext import commands


class Management(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def config(self, ctx):
        await ctx.send_help("config")

    @config.command()
    @has_permissions(administrator=True)
    async def setprefix(self, ctx, prefix: str):
        if await self.bot.cache.set_prefix(prefix, guild=ctx.guild):
            message = f"Command prefix changed to `{prefix}`."
        else:
            message = f"`{prefix}` is your current prefix."

        await ctx.send(content=message)


def setup(bot):
    bot.add_cog(Management(bot))
