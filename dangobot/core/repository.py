from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, Type, Dict, List, Optional

from asyncpg.pool import Pool
from asyncpg.connection import Connection
from asyncpg import Record

from discord import Guild

from django.conf import settings
from django.db.models.base import Model

from .models import Guild as DBGuild
from .database import db_pool as _db_pool


def _get_query_string(args: Dict[str, Any]) -> str:
    return " AND ".join(
        [f"{field[0]} = ${i + 1}" for i, field in enumerate(args.items())]
    )


class RepositoryABCSingleton(
    ABCMeta
):  # pylint: disable=missing-class-docstring
    _instances: Dict[RepositoryABCSingleton, Repository] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(RepositoryABCSingleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]


class Repository(metaclass=RepositoryABCSingleton):
    """An ABC that's the base for all other repositories."""

    db_pool: Pool

    def __init__(self, db_pool: Pool = None) -> None:
        super().__init__()

        if db_pool is None:
            db_pool = _db_pool

        self.db_pool = db_pool

    @property
    @abstractmethod
    def model(self) -> Type[Model]:
        """Returns the Django model corresponding to this repository."""

    @property
    def table_name(self) -> str:
        """Returns the table name for this repository."""
        return self.model._meta.db_table

    @property
    def primary_key(self) -> str:
        """Returns the primary key for this repository's table."""
        return self.model._meta.pk.name  # type: ignore

    async def find_by_id(self, _id: int) -> Any:
        """Finds the object by its ID."""
        conn: Connection
        async with self.db_pool.acquire() as conn:
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
        conn: Connection
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self.table_name} WHERE id=$1", _id
            )

            return int(result.split()[1]) == 1

    async def find_by(self, args: Dict[str, Any]) -> List[Record]:
        """
        Finds records in the table constrained by an arbitrary set of fields.

        The values are sanitized before being sent to the database.

        Parameters
        -----------
        args: Dict[`str`, `any`]
            A dictionary containing the query constraints.

        Returns
        --------
        List[`Record`]
            A list of the fetched records.
        """
        query_string = _get_query_string(args)

        conn: Connection
        async with self.db_pool.acquire() as conn:
            return await conn.fetch(
                f"SELECT * FROM {self.table_name} WHERE {query_string}",
                *args.values(),
            )

    async def find_one_by(self, args: Dict[str, Any]) -> Optional[Record]:
        """
        Analogic to :meth:`find_by`, but fetches only one row from the
        database.

        Parameters
        -----------
        args: Dict[`str`, `any`]
            A dictionary containing the query constraints.

        Returns
        --------
        Optional[`Record`]
            The record fetched from the database, or `None` if there was none.
        """
        query_string = _get_query_string(args)

        conn: Connection
        async with self.db_pool.acquire() as conn:
            return await conn.fetchrow(
                f"SELECT * FROM {self.table_name} WHERE {query_string}",
                *args.values(),
            )

    async def destroy_by(self, args: Dict[str, Any]) -> int:
        """
        Removes records from the database constrained by an arbitrary set of
        fields.

        The values are sanitized before being sent to the database.

        Parameters
        -----------
        args: Dict[`str`, `any`]
            A dictionary containing the query constraints.

        Returns
        --------
        `int`
            The amount of records deleted by the query.
        """
        query_string = _get_query_string(args)

        conn: Connection
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                f"DELETE FROM {self.table_name} WHERE {query_string}",
                *args.values(),
            )

            return int(result.split()[1])

    async def insert(self, args: Dict[str, Any]):
        """
        Inserts an arbitrary set of fields and values into the database.

        The values are sanitized before being inserted.

        Parameters
        -----------
        args: Dict[`str`, `any`]
            A dictionary containing the table fields and their respective
            values.
        """
        keys = ", ".join(args.keys())
        values = ", ".join([f"${i + 1}" for i in range(len(args))])

        conn: Connection
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO {self.table_name} "
                f"({keys}) VALUES ({values})",
                *args.values(),
            )


class GuildRepository(Repository):  # pylint: disable=missing-class-docstring
    @property
    def model(self) -> Type[Model]:
        return DBGuild

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

        await self.insert(
            {
                "id": guild.id,
                "name": guild.name,
                "command_prefix": settings.COMMAND_PREFIX,
            }
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

    async def update_command_prefix(self, guild: Guild, prefix: str) -> bool:
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
