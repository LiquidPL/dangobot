from .errors import DownloadError

import os


async def download_file(http_session, url, path):
    """
    Downloads a file to a given location.
    """

    file_size = 0
    chunk_size = 1024

    error_msgs = {404: "The requested file was not found!"}

    os.makedirs(os.path.dirname(path), exist_ok=True)

    async with http_session.get(url) as resp:
        if resp.status is not 200:
            if resp.status in error_msgs:
                message = error_msgs[resp.status]
            else:
                message = "An error has occured while downloading the file!"

            raise DownloadError(message)

        with open(path, "wb") as f:
            while True:
                chunk = await resp.content.read(1024)
                if not chunk:
                    break

                file_size = file_size + chunk_size
                if file_size > 8 * 2 ** 20:  # 8 MiB
                    f.close()
                    os.remove(path)

                    raise DownloadError(
                        "The provided attachment is larger than 8MB!"
                    )

                f.write(chunk)


async def guild_fetch_or_create(db_pool, guild):
    """
    Attempts to fetch a guild with a given ID from the database,
    or, if none exists, creates it.

    Returns True if a guild was successfully fetched, and False otherwise.
    """
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM core_guild WHERE id = $1", guild.id
        )

        if row is None:
            await conn.execute(
                "INSERT INTO core_guild(id, name) VALUES ($1, $2)",
                guild.id,
                guild.name,
            )

            return False
        else:
            return row
