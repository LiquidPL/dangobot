from typing import List, Type
from asyncpg import Record
from django.db.models.base import Model
from dangobot.roles.models import RoleForVoiceChannel
from dangobot.core.repository import Repository


class RoleForVCRepository(
    Repository
):  # pylint: disable=missing-class-docstring
    @property
    def model(self) -> Type[Model]:
        return RoleForVoiceChannel

    async def find_by_voice_channel(self, voice_channel_id: int) -> Record:
        """Returns the role for a given voice channel."""
        return await self.find_one_by({"voice_channel_id": voice_channel_id})

    async def find_by_guild(self, guild_id: int) -> List[Record]:
        """Returns all role/voice channel links for a given guild."""
        return await self.find_by({"guild_id": guild_id})
