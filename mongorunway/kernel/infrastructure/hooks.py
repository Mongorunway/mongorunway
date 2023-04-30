from __future__ import annotations

__all__: typing.Sequence[str] = (
    "PrioritizedHook",
    "SyncScriptsWithQueues",
    "RecalculateMigrationsChecksum",
    "RaiseIfMigrationChecksumMismatch",
)

import dataclasses
import logging
import typing

from mongorunway.kernel.application.ports.hook import (
    MigrationHook,
    PrioritizedMigrationHook,
)

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.ui import MigrationUI
    from mongorunway.kernel.application.ports.queue import MigrationQueue

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("mongorunway.hooks")


@dataclasses.dataclass(order=True)
class PrioritizedHook(PrioritizedMigrationHook):
    _priority: int = dataclasses.field(compare=True, hash=True)
    _item: MigrationHook = dataclasses.field(compare=False, hash=False)

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def item(self) -> MigrationHook:
        return self._item


class SyncScriptsWithQueues(MigrationHook):
    __slots__: typing.Sequence[str] = ()

    def apply(self, application: MigrationUI, /) -> None:
        for migration in application.get_migrations_from_directory():
            if (
                not application.pending.has_migration(migration)
                and not application.applied.has_migration(migration)
            ):
                # Check for logging
                application.pending.append_migration(migration)

                _LOGGER.info(
                    "%s: migration '%s' with version %s was unsynced and successfully append to pending.",
                    self.__class__.__name__,
                    migration.name,
                    migration.version,
                )


class RecalculateMigrationsChecksum(MigrationHook):
    __slots__: typing.Sequence[str] = ()

    def apply(self, application: MigrationUI, /) -> None:
        def _sync_queue(queue: MigrationQueue, /) -> None:
            for migration in queue.acquire_all_migrations():
                current_migration_state = application.get_migration_from_filename(
                    migration.name,
                )

                if current_migration_state.checksum != migration.checksum:
                    queue.remove_migration(migration.version)
                    queue.append_migration(current_migration_state)

                    _LOGGER.info(
                        "%s: migration file '%s' with version %s is changed, checksum successfully "
                        "recalculated (%s) -> (%s).",
                        self.__class__.__name__,
                        migration.name,
                        migration.version,
                        migration.checksum,
                        current_migration_state.checksum,
                    )

        _sync_queue(application.pending)
        _sync_queue(application.applied)


class RaiseIfMigrationChecksumMismatch(MigrationHook):
    __slots__: typing.Sequence[str] = ()

    def apply(self, application: MigrationUI, /) -> None:
        def _validate_queue(queue: MigrationQueue, /) -> None:
            for migration in queue.acquire_all_migrations():
                current_migration_state = application.get_migration_from_filename(
                    migration.name,
                )
                if current_migration_state.checksum != migration.checksum:
                    _LOGGER.info(
                        "%s: migration file '%s' with version %s is changed, raising...",
                        self.__class__.__name__,
                        migration.name,
                        migration.version,
                    )
                    raise ValueError(f"Migration {migration.name!r} is changed.")  # TODO: custom error

        _validate_queue(application.pending)
        _validate_queue(application.applied)
