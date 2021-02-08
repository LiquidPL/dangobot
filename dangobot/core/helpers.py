import os

from discord import Guild
from django.conf import settings

from .errors import DownloadError

from .database import db_pool


async def download_file(http_session, url, path):
    """
    Downloads a file to a given location.
    """

    file_size = 0
    chunk_size = 1024

    error_msgs = {404: "The requested file was not found!"}

    os.makedirs(os.path.dirname(path), exist_ok=True)

    async with http_session.get(url) as resp:
        if resp.status != 200:
            if resp.status in error_msgs:
                message = error_msgs[resp.status]
            else:
                message = "An error has occured while downloading the file!"

            raise DownloadError(message)

        with open(path, "wb") as file:
            while True:
                chunk = await resp.content.read(1024)
                if not chunk:
                    break

                file_size = file_size + chunk_size
                if file_size > 8 * 2 ** 20:  # 8 MiB
                    file.close()
                    os.remove(path)

                    raise DownloadError(
                        "The provided attachment is larger than 8MB!"
                    )

                file.write(chunk)


async def guild_fetch(guild: Guild):
    """
    Attempts to fetch a guild with a given ID from the database.
    """
    # TODO: move this to a repository
    async with db_pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM core_guild WHERE id = $1", guild.id
        )


async def guild_fetch_or_create(guild: Guild):
    """
    Attempts to fetch a guild with a given ID from the database,
    or, if none exists, creates it.

    Returns True if a guild was successfully fetched, and False otherwise.
    """
    # TODO: move this to a repository
    row = await guild_fetch(guild)

    if row is None:
        async with db_pool.acquire() as conn:
            await conn.execute(
                (
                    "INSERT INTO core_guild(id, name, command_prefix) "
                    "VALUES ($1, $2, $3)"
                ),
                guild.id,
                guild.name,
                settings.COMMAND_PREFIX,
            )

        row = await guild_fetch(guild)

    return row
