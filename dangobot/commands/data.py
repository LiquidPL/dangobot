from typing import NamedTuple


class ParsedCommand(NamedTuple):  # pylint: disable=too-few-public-methods
    """
    Container tuple for the parsed command data to be inserted into
    the database.
    """

    trigger: str
    response: str
    path_relative: str
    filename: str
