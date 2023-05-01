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
"""This module provides implementations of the `Migration` interface."""
from __future__ import annotations

__all__: typing.Sequence[str] = ("BaseMigration",)

import typing

import pymongo

from mongorunway.kernel.domain.migration import Migration

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration_command import MigrationCommand


class BaseMigration(Migration):
    """This class provides methods for upgrading and downgrading a database schema using
    a sequence of MigrationCommand instances.

    Parameters
    ----------
    name : str
        The name of the migration.
    version : int
        The version number of the migration.
    checksum : str
        A hash checksum of the migration contents.
    description : str
        A description of the migration.
    upgrade_commands : sequence of MigrationCommand
        A sequence of commands to upgrade the database schema.
    downgrade_commands : sequence of MigrationCommand
        A sequence of commands to downgrade the database schema.
    """

    __slots__: typing.Sequence[str] = (
        "_name",
        "_version",
        "_checksum",
        "_description",
        "_upgrade_commands",
        "_downgrade_commands",
    )

    def __init__(
        self,
        *,
        name: str,
        version: int,
        checksum: str,
        description: str,
        upgrade_commands: typing.Sequence[MigrationCommand],
        downgrade_commands: typing.Sequence[MigrationCommand],
    ) -> None:
        self._name = name
        self._version = version
        self._checksum = checksum
        self._description = description
        self._upgrade_commands = upgrade_commands
        self._downgrade_commands = downgrade_commands

    @property
    def name(self) -> str:
        """Returns the name of the migration.

        Returns
        -------
        str
            The name of the migration.
        """
        return self._name

    @property
    def version(self) -> int:
        """Get the version of the migration.

        Returns
        -------
        int
            The version of the migration.
        """
        return self._version

    @property
    def checksum(self) -> str:
        """Get the checksum of the migration.

        Returns
        -------
        str
            The checksum of the migration.
        """
        return self._checksum

    @property
    def description(self) -> str:
        """Get the description of the migration.

        Returns
        -------
        str
            The description of the migration.
        """
        return self._description

    @property
    def upgrade_commands(self) -> typing.Sequence[MigrationCommand]:
        """Get the upgrade commands for the migration.

        Returns
        -------
        Sequence[MigrationCommand]
            A sequence of MigrationCommand objects representing the upgrade commands
            for the migration.
        """
        return self._upgrade_commands

    @property
    def downgrade_commands(self) -> typing.Sequence[MigrationCommand]:
        """Get the downgrade commands for the object.

        Returns
        -------
        Sequence[MigrationCommand]
            A sequence of MigrationCommand objects representing the downgrade commands
            for the migration.
        """
        return self._downgrade_commands

    def downgrade(self, client: pymongo.MongoClient[typing.Dict[str, typing.Any]], /) -> None:
        """Downgrade the object to a previous version.

        Parameters
        ----------
        client : pymongo.MongoClient[Dict[str, Any]]
            The MongoDB client object representing the connection to the database.
        """
        for command in self._downgrade_commands:
            command.execute(client)

    def upgrade(self, client: pymongo.MongoClient[typing.Dict[str, typing.Any]], /) -> None:
        """Upgrade the migration to a previous version.

        Parameters
        ----------
        client : pymongo.MongoClient[Dict[str, Any]]
            The MongoDB client object representing the connection to the database.
        """
        for command in self._upgrade_commands:
            command.execute(client)

    def to_mongo_dict(self) -> typing.Dict[str, typing.Any]:
        """Convert the object to a dictionary representation for MongoDB.

        Returns
        -------
        Dict[str, Any]
            A dictionary representation of the object suitable for storing in a
            MongoDB collection.
        """
        return {
            "_id": self.version,
            "name": self.name,
            "version": self.version,
            "checksum": self.checksum,
            "description": self.description,
        }
