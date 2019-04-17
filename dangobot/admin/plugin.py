from discord.ext.commands import Cog, is_owner
from discord.ext import commands

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


def setup(bot):
    bot.add_cog(Admin(bot))
