from discord.ext.commands import CommandError


class DangoError(CommandError):
    """
    Base exception class for the bot.

    All exceptions thrown by the bot are subclassed from here.
    """


class DownloadError(DangoError):
    """
    Exception raised when an error occurs while the bot was downloading a file.
    """
