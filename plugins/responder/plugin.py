from discord.ext import commands
from discord.ext.commands.view import StringView

from .models import Command
from db.models import Server

import asyncio

class Responder:
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, message):
        view = StringView(message.content)
        prefix = await self.bot._get_prefix(message)
        invoked_prefix = prefix

        if not isinstance(prefix, (tuple, list)):
            if not view.skip_string(prefix):
                return
        else:
            invoked_prefix = discord.utils.find(view.skip_string, prefix)
            if invoked_prefix is None:
                return

        trigger = view.get_word()

        try:
            command = Command.objects.get(server=message.server.id, trigger=trigger)

            if command.file:
                await self.bot.send_file(message.channel, command.file.path, content=None)
            else:
                await self.bot.send_message(message.channel, content=command.response)
        except Command.DoesNotExist:
            pass

    @commands.command(pass_context=True)
    @commands.has_permissions(manage_messages=True)
    async def addcommand(self, ctx, trigger : str, response : str):
        server, created = Server.objects.get_or_create(
            id=ctx.message.server.id,
            defaults={'name': ctx.message.server.name}
        )

        command = Command(server=server, trigger=trigger, response=response)

        try:
            command.save()

            await self.bot.send_message(
                ctx.message.channel,
                content='Command `{trigger}` added successfully!'.format(trigger=trigger)
            )
        except Exception:
            await self.bot.send_message(
                ctx.message.channel,
                content="Couldn't add the command `{trigger}`.".format(trigger=trigger)
            )

    @commands.command(pass_context=True)
    @commands.has_permissions(manage_messages=True)
    async def editcommand(self, ctx, trigger : str, response : str):
        try:
            command = Command.objects.get(server=ctx.message.server.id, trigger=trigger)
        except Command.DoesNotExist:
            await self.send_message(
                ctx.message.channel,
                content='Command `{trigger} not found!`'.format(trigger, trigger)
            )
            return

        command.response = response

        try:
            command.save()

            await self.bot.send_message(
                ctx.message.channel,
                content='Command `{trigger}` updated successfully!'.format(trigger=trigger)
            )
        except:
            await self.bot.send_message("Couldn't update command `{trigger}`".format(trigger=trigger))



    @commands.command(pass_context=True)
    @commands.has_permissions(manage_messages=True)
    async def removecommand(self, ctx, trigger : str):
        command = Command.objects.get(server=ctx.message.server.id, trigger=trigger)

        try:
            command.delete()

            await self.bot.send_message(
                ctx.message.channel,
                'Command `{trigger}` deleted successfully!'.format(trigger=trigger)
            )
        except Exception:
            await self.bot.send_message(
                ctx.message.channel,
                "Couldn't delete the command `{trigger}`.".format(trigger=trigger)
            )

def setup(bot):
    bot.add_cog(Responder(bot))
