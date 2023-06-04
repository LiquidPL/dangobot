import os


class FileTooLarge(RuntimeError):
    """
    Exception raised when the downloaded file exceeds the Discord file size
    limit (currently 25 MiB).
    """


async def download_file(http_session, url, path):
    """
    Downloads a file to a given location.
    """

    file_size = 0
    chunk_size = 1024

    os.makedirs(os.path.dirname(path), exist_ok=True)

    async with http_session.get(url, raise_for_status=True) as resp:
        with open(path, "wb") as file:
            while True:
                chunk = await resp.content.read(1024)
                if not chunk:
                    break

                file_size = file_size + chunk_size
                if file_size > 25 * 2**20:  # 8 MiB
                    file.close()
                    os.remove(path)

                    raise FileTooLarge(
                        "The provided attachment is larger than 25MB!"
                    )

                file.write(chunk)
