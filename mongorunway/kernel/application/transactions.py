from __future__ import annotations

__all__: typing.Sequence[str] = (
    "MigrationTransaction",
    "UpgradeTransaction",
    "DowngradeTransaction",
    "TRANSACTION_SUCCESS",
    "TRANSACTION_NOT_APPLIED",
)

import abc
import typing

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.ui import MigrationUI
    from mongorunway.kernel.domain.migration import Migration

TRANSACTION_SUCCESS = 1
TRANSACTION_NOT_APPLIED = 0


class MigrationTransaction(abc.ABC):
    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def apply_migration(self, migration: Migration, /) -> None:
        ...

    @abc.abstractmethod
    def commit(self) -> None:
        ...

    @abc.abstractmethod
    def rollback(self) -> None:
        ...


class UpgradeTransaction(MigrationTransaction):
    __slots__: typing.Sequence[str] = ("_application", "_ctx_migration")

    def __init__(self, application: MigrationUI, /) -> None:
        self._application = application
        self._ctx_migration: typing.Optional[Migration] = None

    def apply_migration(self, migration: Migration, /) -> None:
        self._ctx_migration = migration
        migration.upgrade(self._application.config.connection.mongo_client)

    def commit(self):
        nowait_migration = self._ensure_migration()
        self._application.applied.append_migration(nowait_migration)
        self._application.pending.remove_migration(nowait_migration.version)

    def rollback(self):
        nowait_migration = self._ensure_migration()

        if self._application.applied.has_migration(nowait_migration):
            self._application.applied.remove_migration(nowait_migration.version)

        if not self._application.pending.has_migration(nowait_migration):
            self._application.pending.append_migration(nowait_migration)

    def _ensure_migration(self) -> Migration:
        if self._ctx_migration is None:
            raise ValueError("Migration is not upgraded.")
        return self._ctx_migration


class DowngradeTransaction(MigrationTransaction):
    __slots__: typing.Sequence[str] = ("_application", "_ctx_migration")

    def __init__(self, application: MigrationUI, /) -> None:
        self._application = application
        self._ctx_migration: typing.Optional[Migration] = None

    def apply_migration(self, migration: Migration, /) -> None:
        self._ctx_migration = migration
        migration.downgrade(self._application.config.connection.mongo_client)

    def commit(self):
        nowait_migration = self._ensure_migration()
        self._application.pending.append_migration(nowait_migration)
        self._application.applied.remove_migration(nowait_migration.version)

    def rollback(self):
        nowait_migration = self._ensure_migration()

        if self._application.pending.has_migration(nowait_migration):
            self._application.pending.remove_migration(nowait_migration.version)

        if not self._application.applied.has_migration(nowait_migration):
            self._application.applied.append_migration(nowait_migration)

    def _ensure_migration(self) -> Migration:
        if self._ctx_migration is None:
            raise ValueError("Migration is not upgraded.")
        return self._ctx_migration
