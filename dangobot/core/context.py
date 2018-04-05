from discord.ext import commands


class Context(commands.Context):
    async def send_help(self, command=None):
        cmd = self.bot.get_command('help')
        command = command or self.command.qualified_name

        self.invoked_with = 'help'
        await self.invoke(cmd, command)
