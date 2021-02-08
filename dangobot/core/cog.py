from discord.ext.commands import Cog as BaseCog

from dangobot.core.bot import DangoBot


class Cog(BaseCog):
    """The base class for the bot's cogs/plugins."""

    def __init__(self, bot: DangoBot):
        self.bot = bot
