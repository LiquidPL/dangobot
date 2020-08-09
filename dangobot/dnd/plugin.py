from discord.ext import commands
from discord.ext.commands import Cog

from discord import Embed

import re
import random

DICES = 1
ROLLS = 2
FULL_VALUE = 3


class DnD(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dice_pattern = re.compile(r"([0-9]*)d([0-9]+)")
        self.number_pattern = re.compile(r"([0-9]+)")

    @commands.command()
    async def roll(self, ctx, *, input: str):
        """
        Roll a variable amount of dice, commonly used in\
        tabletop/pen-and-paper RPG games.

        Uses [standard dice\
        notation](https://en.wikipedia.org/wiki/Dice_notation).
        """
        full_value = 0
        results = []

        rolls = re.sub(r"\s+", "", input).split("+")

        if len(rolls) > 20:
            display_format = FULL_VALUE
        elif len(rolls) > 1:
            display_format = ROLLS
        else:  # len(rolls) == 1
            display_format = DICES

        for roll in rolls:
            if roll:
                number_match = self.number_pattern.fullmatch(roll)

                if number_match:
                    full_value += int(number_match.string)
                    continue

                dice_match = self.dice_pattern.fullmatch(roll)

                if not dice_match:
                    await ctx.send("Invalid roll!")
                    return

                roll_value = 0

                if not dice_match.group(1):
                    roll_count = 1
                else:
                    roll_count = int(dice_match.group(1))

                if roll_count > 20:
                    display_format = FULL_VALUE

                for i in range(roll_count):
                    dice_value = random.randint(1, int(dice_match.group(2)))

                    if display_format == DICES:
                        results.append(dice_value)

                    roll_value += dice_value

                if display_format == ROLLS:
                    results.append(roll_value)

                full_value += roll_value

        embed = Embed(title=f"Rolling {input}")

        if not display_format == FULL_VALUE:
            for i, result in enumerate(results, start=1):
                embed.add_field(
                    name=self.roll_string(display_format).format(i),
                    value=result,
                    inline=True,
                )

        embed.add_field(name="**Full value**", value=full_value, inline=False)

        await ctx.send(embed=embed)

    def roll_string(self, format):
        if format == DICES:
            return "Dice {}"
        else:
            return "Roll {}"


def setup(bot):
    bot.add_cog(DnD(bot))
