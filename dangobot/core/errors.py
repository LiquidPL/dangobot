class DangoException(Exception):
    """
    Base exception class for the bot.

    All exceptions thrown by the bot are subclassed from here.
    """

    pass


class DownloadError(DangoException):
    """
    Exception raised when an error occurs while the bot was downloading a file.
    """

    pass
