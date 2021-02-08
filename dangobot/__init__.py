import asyncio

# Instantiating the event loop here to ensure that the bot, and all the module
# level objects (ie. database) are using the same one.
loop = asyncio.get_event_loop()
