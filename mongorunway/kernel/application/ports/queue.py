from __future__ import annotations

__all__: typing.Sequence[str] = ("MigrationQueue",)

import abc
import typing

import pymongo

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration import Migration


class MigrationQueue(abc.ABC):
    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def __len__(self) -> int:
        ...

    @abc.abstractmethod
    def __contains__(self, item: typing.Any, /) -> bool:
        ...

    @abc.abstractmethod
    def has_migration(self, migration: Migration, /) -> bool:
        ...

    @abc.abstractmethod
    def has_migrations(self) -> bool:
        ...

    @abc.abstractmethod
    def has_migration_with_version(self, migration_version, /) -> bool:
        ...

    @abc.abstractmethod
    def acquire_nowait_migration(self) -> typing.Optional[Migration]:
        ...

    @abc.abstractmethod
    def pop_nowait_migration(self) -> typing.Optional[Migration]:
        ...

    @abc.abstractmethod
    def acquire_first_migration(self) -> typing.Optional[Migration]:
        ...

    @abc.abstractmethod
    def acquire_latest_migration(self) -> typing.Optional[Migration]:
        ...

    @abc.abstractmethod
    def acquire_migration(self, migration_version: int, /) -> typing.Optional[Migration]:
        ...

    @abc.abstractmethod
    def append_migration(self, migration: Migration, /) -> int:
        ...

    @abc.abstractmethod
    def remove_migration(self, migration_version: int, /) -> None:
        ...

    @abc.abstractmethod
    def acquire_all_migrations(self, *, sort_by: int = pymongo.ASCENDING) -> typing.Sequence[Migration]:
        ...
