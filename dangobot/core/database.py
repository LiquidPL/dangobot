import asyncpg
from django.db import connection

from dangobot import loop

db_pool = None  # pylint: disable=invalid-name


async def init():  # pylint: disable=missing-function-docstring
    global db_pool  # pylint: disable=global-statement, invalid-name
    db_pool = await asyncpg.create_pool(
        database=connection.settings_dict["NAME"],
        user=connection.settings_dict["USER"],
        password=connection.settings_dict["PASSWORD"],
        host=connection.settings_dict["HOST"],
        port=connection.settings_dict["PORT"],
    )


loop.run_until_complete(init())
