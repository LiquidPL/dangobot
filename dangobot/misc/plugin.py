from discord.ext import commands

import re
import random


class Misc:
    def __init__(self, bot):
        self.bot = bot
        self.roll_pattern = re.compile(r"([0-9]+)d([0-9]+)")
        self.number_pattern = re.compile(r"([0-9]+)")

    @commands.command()
    async def roll(self, ctx, *, input: str):
        ans = 0
        for x in re.sub(r"\s+", "", input).split('+'):
            if x:
                roll = self.number_pattern.fullmatch(x)

                if roll:
                    ans += int(roll.group(1))
                    continue

                roll = self.roll_pattern.fullmatch(x)

                if not roll:
                    await ctx.send('Invalid roll!')
                    return

                for i in range(int(roll.group(1))):
                    ans += random.randint(1, int(roll.group(2)))

        await ctx.send(ans)


def setup(bot):
    bot.add_cog(Misc(bot))
