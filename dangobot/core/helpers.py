import traceback


def format_traceback(exception):
    """
    Format a traceback ready to be posted in a
    Discord embed given an exception.
    """
    trace = traceback.format_exception(
        exception.__class__,
        exception,
        exception.__traceback__
    )

    length = sum(len(el) for el in trace)

    # remove oldest traces until we're under the embed
    # length cap, which is1000, minus 6 characters for
    # codeblock start and end, 4 for a 3 character
    # ellipsis (...) and a newline character
    while length > 990:
        element_length = len(trace[1])
        del trace[1]
        length = length - element_length

    trace.insert(1, '...\n')

    return trace
