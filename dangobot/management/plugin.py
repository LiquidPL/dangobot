from discord.ext import commands
from discord.ext.commands import Context, has_permissions, NoPrivateMessage

from dangobot.core.bot import DangoBot
from dangobot.core.plugin import Cog
from dangobot.core.repository import GuildRepository


class Management(Cog):
    """Configuration of the bot."""

    @commands.group(invoke_without_command=True)
    async def config(
        self, ctx: Context
    ):  # pylint: disable=missing-function-docstring
        await ctx.send_help("config")

    @config.command()
    @has_permissions(administrator=True)
    async def setprefix(self, ctx: Context, prefix: str):
        """Sets a new command prefix for the bot commands."""
        if ctx.guild is None:
            raise NoPrivateMessage("You cannot use this command in a DM")

        if await GuildRepository().set_command_prefix(ctx.guild, prefix):
            message = f"Command prefix changed to `{prefix}`."
        else:
            message = f"`{prefix}` is already your prefix."

        await ctx.send(content=message)


async def setup(bot: DangoBot):  # pylint: disable=missing-function-docstring
    await bot.add_cog(Management(bot))
