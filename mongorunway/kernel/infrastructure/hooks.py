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
"""Module contains a set of hook implementations designed for use in a migration application."""
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
from mongorunway.kernel.domain.migration_exception import MigrationFileChangedError

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.ui import MigrationUI
    from mongorunway.kernel.application.ports.queue import MigrationQueue

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("mongorunway.hooks")


@dataclasses.dataclass(order=True, frozen=True)  # frozen=true is used to generate __hash__ method.
class PrioritizedHook(PrioritizedMigrationHook):
    """Abstract base class for a prioritized migration hook.

    A prioritized migration hook is a wrapper around a `MigrationHook` that allows defining
    a priority level for the hook.

    Parameters
    ----------
    _priority : int
        The priority value of the object.
    _item : MigrationHook
        The migration hook object.

    Notes
    -----
    The hooks with higher priority level will be executed first during the migration process.
    """

    _priority: int = dataclasses.field(compare=True, hash=True)
    """The priority value of the object."""

    _item: MigrationHook = dataclasses.field(compare=False, hash=False)
    """The migration hook object."""

    @property
    def priority(self) -> int:
        """Property for getting the priority of an object.

        Returns
        -------
        int
            The priority value of the object.
        """
        return self._priority

    @property
    def item(self) -> MigrationHook:
        """Property for getting the migration hook item.

        Returns
        -------
        MigrationHook
            The migration hook object.
        """
        return self._item


class SyncScriptsWithQueues(MigrationHook):
    """A migration hook that synchronizes the pending migrations queue with the
    migrations directory.

    This hook checks the migrations directory for new migrations and adds them
    to the pending migrations queue if they are not already applied or pending.
    """

    __slots__: typing.Sequence[str] = ()

    def apply(self, application: MigrationUI, /) -> None:
        """Applies the hook to the migration application.

        Parameters
        ----------
        application: MigrationUI
            The migration application to apply the hook to.
        """
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
    """A migration hook that recalculates the checksum of migrations and updates the
    migration queue accordingly.

    This hook checks the checksum of each migration file in the pending and applied
    migration queues. If the current checksum of the migration file is different from
    the one stored in the migration state object, it recalculates the checksum and updates
    the migration state and queue accordingly.
    """

    __slots__: typing.Sequence[str] = ()

    def apply(self, application: MigrationUI, /) -> None:
        """Applies the hook to the migration application.

        Parameters
        ----------
        application: MigrationUI
            The migration application to apply the hook to.
        """
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
    """A migration hook that raises an error if a migration file's checksum is changed."""

    __slots__: typing.Sequence[str] = ()

    def apply(self, application: MigrationUI, /) -> None:
        """Applies the hook to the migration application.

        Parameters
        ----------
        application: MigrationUI
            The migration application to apply the hook to.
        """
        def _validate_queue(queue: MigrationQueue, /) -> None:
            for migration in queue.acquire_all_migrations():
                current_migration_state = application.get_migration_from_filename(
                    migration.name,
                )
                if current_migration_state.checksum != migration.checksum:
                    _LOGGER.error(
                        "%s: migration file '%s' with version %s is changed, raising...",
                        self.__class__.__name__,
                        migration.name,
                        migration.version,
                    )
                    raise MigrationFileChangedError(f"Migration {migration.name!r} is changed.")

        _validate_queue(application.pending)
        _validate_queue(application.applied)
