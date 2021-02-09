from typing import NamedTuple


# TODO: remove the inherit-non-clas disable once this is fixed in pylint
class ParsedCommand(
    NamedTuple
):  # pylint: disable=inherit-non-class, too-few-public-methods
    """
    Container tuple for the parsed command data to be inserted into
    the database.
    """

    trigger: str
    response: str
    path_relative: str
    filename: str
