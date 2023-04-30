from __future__ import annotations

__all__: typing.Sequence[str] = ("BaseMigration",)

import typing

import pymongo

from mongorunway.kernel.domain.migration import Migration

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration_command import MigrationCommand


class BaseMigration(Migration):
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
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def checksum(self):
        return self._checksum

    @property
    def description(self):
        return self._description

    @property
    def upgrade_commands(self) -> typing.Sequence[MigrationCommand]:
        return self._upgrade_commands

    @property
    def downgrade_commands(self) -> typing.Sequence[MigrationCommand]:
        return self._downgrade_commands

    def downgrade(self, client: pymongo.MongoClient[typing.Dict[str, typing.Any]], /) -> None:
        for command in self._downgrade_commands:
            command.execute(client)

    def upgrade(self, client: pymongo.MongoClient[typing.Dict[str, typing.Any]], /) -> None:
        for command in self._upgrade_commands:
            command.execute(client)

    def to_mongo_dict(self) -> typing.Dict[str, typing.Any]:
        return {
            "_id": self.version,
            "name": self.name,
            "version": self.version,
            "checksum": self.checksum,
            "description": self.description,
        }
