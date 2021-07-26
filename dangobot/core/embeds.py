from datetime import datetime
from typing import Any, Dict, Optional, Union

from discord.colour import Colour
from discord.embeds import Embed as DiscordEmbed


class EmbedFormatter:
    """
    A class that facilitates definition of custom embeds with preset default
    arguments, which can be further overriden by the :meth:`format` method.

    You can declare default values for all arguments supported by the
    :class:`discord.embeds.Embed` constructor, by setting them as class
    attributes.

    Attributes
    ----------------
    icon: Optional[str]
        An icon (usually an emoji) that is displayed alongside the embed's
        title.
    """

    title: Optional[str]
    description: Optional[str]
    type: Optional[str]
    url: Optional[str]
    timestamp: Optional[datetime]
    colour: Union[Colour, int]
    icon: Optional[str]

    __slots__ = (
        "title",
        "description",
        "type",
        "url",
        "timestamp",
        "colour",
        "icon",
    )

    _vanilla_embed_keys = (
        "title",
        "description",
        "type",
        "url",
        "timestamp",
        "colour",
        "color",
    )

    def prepare_arguments(self, **kwargs) -> Dict[str, Any]:
        """
        Prepares the list of arguments to be passed into the embed constructor,
        by taking the default arguments set in class attributes, and merging
        them with the incoming ones.

        This method can be overriden by subclasses to customize this process,
        or add any additional arguments.
        """
        # filter default args to contain only values a vanilla embed accepts
        defaults = {
            key: getattr(self, key)
            for key in self.__slots__
            if key in self._vanilla_embed_keys and hasattr(self, key)
        }

        arguments = defaults | kwargs

        if self.icon is not None and "title" in arguments:
            arguments["title"] = f"{self.icon} {arguments['title']}"

        return arguments

    def format(self, **kwargs) -> DiscordEmbed:
        """
        Returns a formatted embed.

        Returns
        -------
        :class:`discord.embeds.Embed`
            The formatted embed.
        """
        arguments = self.prepare_arguments(**kwargs)

        return DiscordEmbed(**arguments)


class InfoEmbedFormatter(EmbedFormatter):
    """
    Generic informational embed, for instance shown on successful completion
    of some operation.
    """

    icon = "ℹ️"
    colour = Colour.blue()


class ErrorEmbedFormatter(EmbedFormatter):
    """
    An embed used for error messages.

    Arguments
    ---------
    ctx: Optional[discord.ext.commands.context.Context]
        The command execution context that caused this error.
    """

    icon = "🛑"
    colour = Colour.red()
