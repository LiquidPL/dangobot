from typing import Optional
from asyncpg.exceptions import UniqueViolationError
from discord import Member, VoiceState, Role, VoiceChannel, Embed
from discord.ext import commands
from discord.ext.commands.context import Context

from dangobot.core.bot import DangoBot
from dangobot.core.cog import Cog
from dangobot.roles.repository import RoleForVCRepository


class Roles(Cog):
    """A plugin that handles automatic user role assignment."""

    @Cog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        """
        Event handler for processing voice channel joins/parts.

        Will assign a role to the user to provide access to an appriopriate
        text channel on joining a voice channel, and remove it on parting,
        provided that the voice-text channel pair has been configured in
        the database for the given guild.
        """

        async def get_role(channel: VoiceChannel) -> Optional[Role]:
            role_record = await RoleForVCRepository().find_by_voice_channel(
                voice_channel_id=channel.id
            )

            if role_record is None:
                return None

            return channel.guild.get_role(role_record["role_id"])

        if before.channel and (role := await get_role(before.channel)):
            await member.remove_roles(role)

        if after.channel and (role := await get_role(after.channel)):
            await member.add_roles(role)

    @commands.group(name="roleconfig", invoke_without_command=True)
    async def roles(self, ctx: Context):
        """Management of automatically assigned roles."""
        await ctx.send_help("roleconfig")

    @roles.group(invoke_without_command=True)
    async def voice(self, ctx: Context):
        """Management of linked roles and voice channels."""
        await ctx.send_help("roleconfig voice")

    @voice.command(name="link")
    async def voice_link(
        self, ctx: Context, role: Role, voice_channel: VoiceChannel
    ):
        """
        Links a role and a voice channel.

        Whenever an user joins that voice channel, they will be automatically\
        assigned the linked role. This can be used for things like a text\
        channel used to chat with voice members when they're unable to speak.
        """
        try:
            await RoleForVCRepository().insert(
                {
                    "guild_id": voice_channel.guild.id,
                    "role_id": role.id,
                    "voice_channel_id": voice_channel.id,
                }
            )
        except UniqueViolationError:
            await ctx.send(
                f"Role <@&{role.id}> and voice channel"
                f" **<#{voice_channel.id}>** are already linked!"
            )
            return

        await ctx.send(
            f"Role <@&{role.id}> and voice channel"
            f" **<#{voice_channel.id}>** linked successfully!"
        )

    @voice.command(name="unlink")
    async def voice_unlink(
        self, ctx: Context, role: Role, voice_channel: VoiceChannel
    ):
        """Unlinks a role and a voice channel."""
        amount = await RoleForVCRepository().destroy_by(
            {"role_id": role.id, "voice_channel_id": voice_channel.id}
        )

        if amount > 0:
            await ctx.send(
                f"Role <@&{role.id}> and voice channel "
                f"**<#{voice_channel.id}>** unlinked successfully!"
            )
        elif amount == 0:
            await ctx.send(
                f"Role <@&{role.id}> and voice channel "
                f"**<#{voice_channel.id}>** are not linked."
            )

    @voice.command(name="list")
    async def voice_list(self, ctx: Context):
        """Lists all linked roles and voice channels."""
        roles = await RoleForVCRepository().find_by_guild(ctx.guild.id)

        embed = Embed()
        embed.title = "Linked roles and voice channels"
        embed.description = "\n".join(
            [
                f"- <@&{linked['role_id']}> - "
                f" **<#{linked['voice_channel_id']}>**"
                for linked in roles
            ]
        )

        if len(roles) == 0:
            embed.description = \
                "There are no linked roles and voice channels right now."

        await ctx.send(embed=embed)


def setup(bot: DangoBot):  # pylint: disable=missing-function-docstring
    bot.add_cog(Roles(bot))
