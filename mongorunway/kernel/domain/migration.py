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
    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def name(self):
        ...

    @property
    @abc.abstractmethod
    def version(self):
        ...

    @property
    @abc.abstractmethod
    def checksum(self):
        ...

    @property
    @abc.abstractmethod
    def description(self):
        ...

    @property
    @abc.abstractmethod
    def upgrade_commands(self) -> typing.Sequence[MigrationCommand]:
        ...

    @property
    @abc.abstractmethod
    def downgrade_commands(self) -> typing.Sequence[MigrationCommand]:
        ...

    @abc.abstractmethod
    def downgrade(self, client: pymongo.MongoClient[typing.Dict[str, typing.Any]], /) -> None:
        ...

    @abc.abstractmethod
    def upgrade(self, client: pymongo.MongoClient[typing.Dict[str, typing.Any]], /) -> None:
        ...

    @abc.abstractmethod
    def to_mongo_dict(self) -> typing.Dict[str, typing.Any]:
        ...


@dataclasses.dataclass
class MigrationReadModel:
    name: str = dataclasses.field()
    version: int = dataclasses.field()
    checksum: str = dataclasses.field()
    description: str = dataclasses.field()

    @classmethod
    def from_dict(cls, mapping):
        mapping.pop("_id", None)  # For mongo records
        return cls(**mapping)

    @classmethod
    def from_migration(cls, migration):
        return cls(
            name=migration.name,
            version=migration.version,
            checksum=migration.checksum,
            description=migration.description,
        )
