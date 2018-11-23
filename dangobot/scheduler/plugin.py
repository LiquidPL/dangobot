from .models import Task

from discord.ext import commands

import logging

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, bot):
        self.bot = bot
        self.table = Task._meta.db_table

    async def get_next_wakeup_time(self):
        """
        Retrieves the timestamp of the closest task to the current time.
        """
        async with self.bot.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT scheduled_time FROM {self.table} "
                "WHERE scheduled_time > current_timestamp "
                "ORDER BY scheduled_time ASC"
            )

            return row['scheduled_time']

    async def demo(self):
        logger.info('test')

    @commands.command()
    async def test(self, ctx):
        timestamp = await self.get_next_wakeup_time()
        logger.info(timestamp)
        await ctx.send(content=timestamp)


def setup(bot):
    bot.add_cog(Scheduler(bot))
