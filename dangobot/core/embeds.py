from typing import Optional
from discord import Embed as DiscordEmbed
from discord.colour import Colour


class BaseEmbed(DiscordEmbed):
    """
    Base class for the bot's custom embeds.

    Provides a way to specify an emoji icon that is displayed alongisde the
    embed's title.

    Class Attributes
    ----------------
    icon: Optional[str]
        Icon that is being displayed alongside the embed's title.
    """

    icon: Optional[str] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.configure()

    def configure(self):
        """Use this method to set default properties for this embed."""

    def to_dict(self):
        embed = super().to_dict()

        if self.icon is not None and "title" in embed:
            embed["title"] = f"{self.icon} {embed['title']}"

        return embed


class InfoEmbed(BaseEmbed):
    """
    Generic informational embed, for instance shown on successful completion
    of some operation.
    """

    icon = "ℹ️"

    def configure(self):
        self.colour = Colour.blue()


class ErrorEmbed(BaseEmbed):
    """An embed used for error messages."""

    icon = "🛑"

    def configure(self):
        self.colour = Colour.red()
