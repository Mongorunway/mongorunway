# Copyright (c) 2023 Animatea
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""The main interface for managing migrations is the `Migration` class.
It represents a single migration that can be applied or reverted in a database.
"""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "Migration",
    "MigrationReadModel",
)

import abc
import dataclasses
import typing

import pymongo

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration_command import MigrationCommand


class Migration(abc.ABC):
    """Interface for defining database migrations.

    Notes
    -----
    This interface defines the methods and properties required to define a database
    migration. A migration is a set of instructions for modifying a database schema
    to support new features or fix issues.

    Each migration consists of a version number, a name, and one or more commands
    that describe how to upgrade or downgrade the schema.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Returns the name of the migration.

        Returns
        -------
        str
            The name of the migration.
        """
        ...

    @property
    @abc.abstractmethod
    def version(self) -> int:
        """Get the version of the migration.

        Returns
        -------
        int
            The version of the migration.
        """
        ...

    @property
    @abc.abstractmethod
    def checksum(self) -> str:
        """Get the checksum of the migration.

        Returns
        -------
        str
            The checksum of the migration.
        """
        ...

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Get the description of the migration.

        Returns
        -------
        str
            The description of the migration.
        """
        ...

    @property
    @abc.abstractmethod
    def upgrade_commands(self) -> typing.Sequence[MigrationCommand]:
        """Get the upgrade commands for the migration.

        Returns
        -------
        Sequence[MigrationCommand]
            A sequence of MigrationCommand objects representing the upgrade commands
            for the migration.
        """
        ...

    @property
    @abc.abstractmethod
    def downgrade_commands(self) -> typing.Sequence[MigrationCommand]:
        """Get the downgrade commands for the object.

        Returns
        -------
        Sequence[MigrationCommand]
            A sequence of MigrationCommand objects representing the downgrade commands
            for the migration.
        """
        ...

    @abc.abstractmethod
    def downgrade(self, client: pymongo.MongoClient[typing.Dict[str, typing.Any]], /) -> None:
        """Downgrade the object to a previous version.

        Parameters
        ----------
        client : pymongo.MongoClient[Dict[str, Any]]
            The MongoDB client object representing the connection to the database.
        """
        ...

    @abc.abstractmethod
    def upgrade(self, client: pymongo.MongoClient[typing.Dict[str, typing.Any]], /) -> None:
        """Upgrade the migration to a previous version.

        Parameters
        ----------
        client : pymongo.MongoClient[Dict[str, Any]]
            The MongoDB client object representing the connection to the database.
        """
        ...

    @abc.abstractmethod
    def to_mongo_dict(self) -> typing.Dict[str, typing.Any]:
        """Convert the object to a dictionary representation for MongoDB.

        Returns
        -------
        Dict[str, Any]
            A dictionary representation of the object suitable for storing in a
            MongoDB collection.
        """
        ...


@dataclasses.dataclass
class MigrationReadModel:
    """Represents a read model of a migration that provides information about the migration.

    Attributes
    ----------
    name : str
        The name of the migration.
    version : int
        The version of the migration.
    checksum : str
        The checksum of the migration.
    description : str
        The description of the migration.
    """

    name: str = dataclasses.field()
    """The name of the migration."""

    version: int = dataclasses.field()
    """The version of the migration."""

    checksum: str = dataclasses.field()
    """The checksum of the migration."""

    description: str = dataclasses.field()
    """The description of the migration."""

    @classmethod
    def from_dict(cls, mapping: typing.MutableMapping[str, typing.Any], /) -> MigrationReadModel:
        """Create a MigrationReadModel instance from a dictionary.

        Parameters
        ----------
        mapping : typing.MutableMapping[str, typing.Any]
            A dictionary containing the attributes of the migration.

        Returns
        -------
        MigrationReadModel
            An instance of MigrationReadModel initialized with the attributes
            from the dictionary.
        """
        mapping.pop("_id", None)  # For mongo records
        return cls(**mapping)

    @classmethod
    def from_migration(cls, migration: Migration, /) -> MigrationReadModel:
        """Create a MigrationReadModel instance from a Migration instance.

        Parameters
        ----------
        migration : Migration
            A Migration instance to create the MigrationReadModel instance from.

        Returns
        -------
        MigrationReadModel
            An instance of MigrationReadModel initialized with the attributes
            from the Migration instance.
        """
        return cls(
            name=migration.name,
            version=migration.version,
            checksum=migration.checksum,
            description=migration.description,
        )
