from discord.ext.commands import Cog, has_permissions
from discord.ext import commands

from dangobot.core.models import Guild


class Management(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def config(self, ctx):
        await ctx.send_help("config")

    @config.command()
    @has_permissions(administrator=True)
    async def setprefix(self, ctx, prefix: str):
        async with self.bot.db_pool.acquire() as conn:
            result = await conn.execute(
                f"UPDATE {Guild._meta.db_table} "
                "SET command_prefix = $1 "
                "WHERE id = $2",
                prefix,
                ctx.guild.id,
            )

        if int(result.split()[1]) == 1:
            self.bot.prefixes[ctx.guild.id] = prefix
            await ctx.send(content=f"Command prefix changed to `{prefix}`")


def setup(bot):
    bot.add_cog(Management(bot))
