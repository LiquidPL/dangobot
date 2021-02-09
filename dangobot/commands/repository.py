from typing import Any, List

from asyncpg.connection import Connection
from dangobot.core.repository import Repository

from dangobot.core.models import Guild

from .models import Command as DBCommand
from .data import ParsedCommand


class CommandRepository(Repository):  # pylint: disable=missing-class-docstring
    @property
    def table_name(self) -> str:
        return DBCommand._meta.db_table

    @property
    def primary_key(self) -> str:
        return DBCommand._meta.pk.name

    async def find_by_trigger(self, trigger: str, guild: Guild) -> Any:
        """Finds a command from a given guild by its text trigger."""
        async with self.db_pool.acquire() as conn:
            conn: Connection

            return await conn.fetchrow(
                f"SELECT * FROM {self.table_name} "
                "WHERE guild_id = $1 AND trigger = $2",
                guild.id,
                trigger,
            )

    async def find_all_from_guild(self, guild: Guild) -> List[Any]:
        """Returns a list of all custom commands defined for a given guild."""
        async with self.db_pool.acquire() as conn:
            conn: Connection

            return await conn.fetch(
                f"SELECT trigger FROM {self.table_name} "
                "WHERE guild_id = $1 ORDER BY trigger ASC",
                guild.id,
            )

    async def add_to_guild(self, guild: Guild, command: ParsedCommand) -> None:
        """Inserts a command for a given guild into the database."""
        async with self.db_pool.acquire() as conn:
            conn: Connection

            await conn.execute(
                f"INSERT INTO {self.table_name}"
                "(guild_id, trigger, response, file, original_file_name) "
                "VALUES ($1, $2, $3, $4, $5)",
                guild.id,
                *command,
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
