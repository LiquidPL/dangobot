from typing import Any, List

from asyncpg.connection import Connection
from asyncpg.types import Type
from django.db.models.base import Model
from dangobot.core.repository import Repository

from dangobot.core.models import Guild

from .models import Command as DBCommand
from .data import ParsedCommand


class CommandRepository(Repository):  # pylint: disable=missing-class-docstring
    @property
    def model(self) -> Type[Model]:
        return DBCommand

    async def find_by_trigger(self, trigger: str, guild: Guild) -> Any:
        """Finds a command from a given guild by its text trigger."""
        conn: Connection
        async with self.db_pool.acquire() as conn:
            return await conn.fetchrow(
                f"SELECT * FROM {self.table_name} "
                "WHERE guild_id = $1 AND trigger = $2",
                guild.id,
                trigger,
            )

    async def find_all_from_guild(self, guild: Guild) -> List[Any]:
        """Returns a list of all custom commands defined for a given guild."""
        conn: Connection
        async with self.db_pool.acquire() as conn:
            return await conn.fetch(
                f"SELECT trigger FROM {self.table_name} "
                "WHERE guild_id = $1 ORDER BY trigger ASC",
                guild.id,
            )

    async def add_to_guild(self, guild: Guild, command: ParsedCommand) -> None:
        """Inserts a command for a given guild into the database."""

        await self.insert(
            {
                "guild_id": guild.id,
                "trigger": command.trigger,
                "response": command.response,
                # this column is named file because of Django model
                # limitations, it actually contains the path to the file
                # on the server
                "file": command.path_relative,
                "original_file_name": command.filename,
            }
        )

    async def update_in_guild(
        self, guild: Guild, command: ParsedCommand
    ) -> bool:
        """
        Updates an existing command for a given guild.

        Returns `true` if the update was successful, or `false` when it wasn't.
        """
        async with self.db_pool.acquire() as conn:
            result: str = await conn.execute(
                f"UPDATE {self.table_name} "
                "SET response = $3, file = $4, original_file_name = $5"
                "WHERE guild_id = $1 AND trigger = $2",
                guild.id,
                *command,
            )

            return int(result.split()[1]) == 1

    async def delete_from_guild(self, trigger: str, guild: Guild) -> bool:
        """
        Deletes a command from a guild given its trigger.

        Returns `true` if the delete was successful, or `false` when it wasn't.
        """
        async with self.db_pool.acquire() as conn:
            result: str = await conn.execute(
                f"DELETE FROM {self.table_name} "
                "WHERE guild_id = $1 AND trigger = $2",
                guild.id,
                trigger,
            )

            return int(result.split()[1]) == 1
