import re
import random
from typing import List, Match, Tuple

from discord import Embed
from discord.ext import commands
from discord.ext.commands import Context

from dangobot.core.bot import DangoBot
from dangobot.core.plugin import Cog
from dangobot.core.errors import DangoError


DICES = 1
ROLLS = 2
FULL_VALUE = 3


roll_pattern = re.compile(r"([0-9]*)d([0-9]+)")
number_pattern = re.compile(r"([0-9]+)")


class InvalidRoll(DangoError):
    """
    Thrown whenever the roll string passed to
    `:func:DnD.process_roll` is invalid.
    """


class DnD(Cog):
    """
    Contains functionality related to tabletop/pen-and-paper role-playing
    games.
    """

    @commands.command()
    async def roll(self, ctx: Context, *, roll_string: str):
        """
        Roll a variable amount of dice, commonly used in\
        tabletop/pen-and-paper role-playing games.

        Uses [standard dice\
        notation](https://en.wikipedia.org/wiki/Dice_notation).
        """
        full_value = 0
        results = []

        rolls = re.sub(r"\s+", "", roll_string).split("+")

        if len(rolls) > 20:
            display_format = FULL_VALUE
        elif len(rolls) > 1:
            display_format = ROLLS
        else:  # len(rolls) == 1
            display_format = DICES

        for roll in rolls:
            if not roll:
                continue

            (value, rolled_values) = self.process_roll(roll)

            full_value += value

            if len(rolled_values) > 20:
                display_format = FULL_VALUE
            elif len(rolls) == 1:
                results = rolled_values
            else:
                results.append(value)

        embed = Embed(title=f"Rolling {roll_string}")

        if not display_format == FULL_VALUE and len(results) > 1:
            for i, result in enumerate(results, start=1):
                embed.add_field(
                    name=f"Dice {i}"
                    if display_format == DICES
                    else f"Roll {i}",
                    value=result,
                    inline=True,
                )

        embed.add_field(name="**Full value**", value=full_value, inline=False)

        await ctx.send(embed=embed)

    @staticmethod
    def calculate_roll(roll: Match) -> Tuple[int, List[int]]:
        """
        Calculates the random values of a single roll.

        Returns a tuple with the first element being the rolled value,
        and the second being a list of all rolls.
        """
        roll_value = 0
        results = []

        if not roll.group(1):
            roll_count = 1
        else:
            roll_count = int(roll.group(1))

        for _ in range(roll_count):
            dice_roll_value = random.randint(1, int(roll.group(2)))

            results.append(dice_roll_value)
            roll_value += dice_roll_value

        return (roll_value, results)

    def process_roll(self, roll: str) -> Tuple[int, List[int]]:
        """
        Parses a single roll, and returns its calculated value.

        If the roll contains just a number, without any roll notation, it's
        returned as is.
        """
        number_match = number_pattern.fullmatch(roll)

        if number_match:
            number = int(number_match.string)
            return (number, [number])

        roll_match = roll_pattern.fullmatch(roll)

        if not roll_match:
            raise InvalidRoll("Invalid roll!")

        return self.calculate_roll(roll_match)


async def setup(bot: DangoBot):  # pylint: disable=missing-function-docstring
    await bot.add_cog(DnD(bot))
