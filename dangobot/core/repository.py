from abc import ABCMeta, abstractmethod
from typing import Any

from asyncpg.pool import Pool
from asyncpg.connection import Connection

from discord import Guild

from django.conf import settings

from .models import Guild as DBGuild
from .database import db_pool as _db_pool


class RepositoryABCSingleton(
    ABCMeta
):  # pylint: disable=missing-class-docstring
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(RepositoryABCSingleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]


class Repository(metaclass=RepositoryABCSingleton):
    """An ABC that's the base for all other repositories."""

    def __init__(self, db_pool: Pool = None) -> None:
        super().__init__()

        if db_pool is None:
            db_pool = _db_pool

        self.db_pool = db_pool

    @property
    @abstractmethod
    def table_name(self) -> str:
        """Returns the table name for this repository."""

    @property
    @abstractmethod
    def primary_key(self) -> str:
        """Returns the primary key for this repository's table."""

    async def find_by_id(self, _id: int) -> Any:
        """Finds the object by its ID."""
        async with self.db_pool.acquire() as conn:
            conn: Connection
            return await conn.fetchrow(
                f"SELECT * FROM {self.table_name} WHERE {self.primary_key}=$1",
                _id,
            )

    async def destroy_by_id(self, _id: int) -> bool:
        """
        Removes a record from the database by its ID.

        Returns `true` if the delete was successful, or `false` when it wasn't
        (for instance, when there was no record with a given ID).
        """

        async with self.db_pool.acquire() as conn:
            conn: Connection

            result = await conn.execute(
                f"DELETE FROM {self.table_name} WHERE id=$1", _id
            )

            return int(result.split()[1]) == 1


class GuildRepository(Repository):  # pylint: disable=missing-class-docstring
    @property
    def table_name(self) -> str:
        return DBGuild._meta.db_table

    @property
    def primary_key(self) -> str:
        return DBGuild._meta.pk.name

    async def create_from_gateway_response(self, guild: Guild) -> Any:
        """
        Inserts a guild into the database based on a response from
        the Discord gateway.

        If a guild with the given ID exists in the database already,
        it is fetched and returned instead.
        """
        existing_guild = await self.find_by_id(guild.id)

        if existing_guild:
            return existing_guild

        async with self.db_pool.acquire() as conn:
            await conn.execute(
                (
                    f"INSERT INTO {self.table_name}(id, name, command_prefix) "
                    "VALUES ($1, $2, $3)"
                ),
                guild.id,
                guild.name,
                settings.COMMAND_PREFIX,
            )

        return await self.find_by_id(guild.id)

    async def update_from_gateway_response(self, guild: Guild) -> bool:
        """
        Updates a guild record that's already in the database based on a
        response from the Discord gateway.

        Returns `true` if the update was successful, or `false` when it wasn't.
        """
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                f"UPDATE {self.table_name} SET name = $1 WHERE id = $2",
                guild.name,
                guild.id,
            )

            return int(result.split()[1]) == 1

    async def update_command_prefix(self, guild: Guild, prefix: str) -> None:
        """Updates the command prefix for a given guild."""

        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                f"UPDATE {self.table_name} "
                "SET command_prefix = $1 "
                "WHERE id = $2",
                prefix,
                guild.id,
            )

            return int(result.split()[1]) == 1


__all__ = ["Repository", "GuildRepository"]
