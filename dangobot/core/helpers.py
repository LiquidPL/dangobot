from django.conf import settings

import os
import logging
import random
import string

logger = logging.getLogger(__name__)

async def random_name():
    yield ''.join([random.choice(
        '{}{}'.format(string.ascii_letters, string.digits)
    ) for i in range(8)])

async def save_file(url, path):
    [directory, filename] = path.rsplit('/', 1)

    while os.path.exists(path):
        path = '{}/{}_{}'.format(directory, await random_name(), filename)

    absolute_path = os.path.join(settings.MEDIA_ROOT, path)

    logger.info(absolute_path)

    file = open(absolute_path, 'wb')

    async with self.bot.http_session.get(file_url) as r:
        while True:
            chunk = await r.content.read(1024)
            if not chunk:
                break

            file.write(chunk)

    yield file
