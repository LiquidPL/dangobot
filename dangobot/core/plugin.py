from discord import Embed
from discord.ext import commands
from discord.ext.commands import Context, Cog as BaseCog

from dateutil.parser import isoparse

from django.conf import settings

from dangobot.core.bot import DangoBot


class Cog(BaseCog):
    """The base class for the bot's cogs/plugins."""

    def __init__(self, bot: DangoBot):
        self.bot = bot


class Core(Cog):
    """Contains commands that provide the core bot functionality."""

    @commands.command()
    async def about(self, ctx: Context) -> None:
        """
        Sends an embed containing information about the bot and the
        currently running version of it.
        """
        version = settings.BUILD_VERSION or "dev"
        build_date = (
            isoparse(settings.BUILD_DATE) if settings.BUILD_DATE else None
        )

        embed = Embed()
        embed.title = "DangoBot"
        embed.set_thumbnail(url=self.bot.user.avatar_url)

        embed.description = f"Version **{version}**"

        if build_date:
            embed.description += (
                f", built on {build_date.strftime('%A, %Y-%m-%d, %H:%M:%S%z')}"
            )

        if await self.bot.is_owner(ctx.author):
            embed.add_field(
                name="Installed apps:",
                value="\n".join(
                    filter(
                        lambda app: app.startswith("dangobot."),
                        settings.INSTALLED_APPS,
                    )
                ),
            )

        await ctx.send(embed=embed)


def setup(bot: DangoBot):  # pylint: disable=missing-function-docstring
    bot.add_cog(Core(bot))
