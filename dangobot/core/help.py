import itertools
import re

from discord.ext.commands import HelpCommand
from discord import Embed


class DangoHelpCommand(HelpCommand):  # pylint: disable=missing-class-docstring
    embed: Embed  # initialized in `prepare_help_command`

    def __init__(self, **options):
        self.sort_commands = options.pop("sort_commands", True)
        self.commands_heading = options.pop(
            "commands_heading", "Available commands:"
        )
        self.no_category = options.pop("no_category", "No category")

        super().__init__(**options)

    async def prepare_help_command(self, ctx, command=None, /):
        self.embed = Embed()

        await super().prepare_help_command(ctx, command)

    async def send_bot_help(self, mapping, /):
        ctx = self.context
        bot = ctx.bot

        if bot.user is None:
            return

        self.embed.title = f"{bot.user.name} Help"
        self.embed.set_thumbnail(url=bot.user.display_avatar)

        def get_category(command):
            cog = command.cog
            return f"{cog.qualified_name}:" if cog else self.no_category

        commands = await self.filter_commands(
            bot.commands, sort=True, key=get_category
        )
        to_iterate = itertools.groupby(commands, key=lambda x: x.cog)

        for cog, commands in to_iterate:
            description = ", ".join(
                map(lambda x: f"{self.context.clean_prefix}{x.name}", commands)
            )

            self.embed.add_field(
                name=cog.qualified_name if cog else self.no_category,
                value=self.process_newlines(description),
                inline=False,
            )

        await self.send_embed()

    async def send_cog_help(self, cog, /):
        self.embed.title = cog.qualified_name

        if cog.description:
            self.embed.description = self.process_newlines(cog.description)

        commands = await self.filter_commands(
            cog.get_commands(), sort=self.sort_commands
        )

        self.add_commands(commands)

        await self.send_embed()

    async def send_group_help(self, group, /):
        self.format_command(group)

        commands = await self.filter_commands(
            group.commands, sort=self.sort_commands
        )

        self.add_commands(commands)

        await self.send_embed()

    async def send_command_help(self, command, /):
        self.format_command(command)
        await self.send_embed()

    def format_command(self, command):
        """Formats the help text for the given command."""
        self.embed.title = self.get_command_signature(command)
        self.embed.description = self.process_newlines(
            f"{command.description}\n{self.command_help(command)}"
        )

    def add_commands(self, commands):
        """Adds help text for commands in the argument to the embed."""
        if self.embed.description:
            self.embed.description += f"\n\n{self.commands_heading}"
        else:
            self.embed.description = self.commands_heading

        for command in commands:
            self.embed.add_field(
                name=command.name,
                value=self.command_help(command, brief=True),
                inline=False,
            )

    async def send_embed(self):
        """Sends the embed to its target destination."""
        await self.get_destination().send(embed=self.embed)

    @staticmethod
    def command_help(command, brief=False):
        """
        Returns the help text for a given command.

        Arguments:
            brief (bool): Whether it should return the brief or full version
                    of the help text.
        """
        help_text = command.help

        if brief:
            help_text = command.short_doc

        if help_text == "":
            help_text = "No help message specified."

        return help_text

    @staticmethod
    def process_newlines(string):
        """
        Makes the docstrings used for command help descriptions more conformant
        with Markdown (in this case the backslash creating a line break).
        """
        return re.sub(r"\\\n", "", string)
