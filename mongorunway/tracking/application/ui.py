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
"""The module contains a class that represents a migration application, each of its
actions is recorded in a migration audit log.
"""
from __future__ import annotations

__all__: typing.Sequence[str] = ("TracedMigrationUI",)

import typing

from mongorunway.kernel.application.ui import MigrationUI
from mongorunway.kernel.domain.migration import MigrationReadModel
from mongorunway.tracking.domain.auditlog_entry import (
    BulkMigrationDowngraded,
    BulkMigrationUpgraded,
    MigrationDowngraded,
    MigrationUpgraded,
    PendingMigrationAdded,
    PendingMigrationRemoved,
)

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.config import ApplicationConfig
    from mongorunway.kernel.application.ports.queue import MigrationQueue
    from mongorunway.kernel.application.ui import ApplicationSession
    from mongorunway.kernel.domain.migration import Migration
    from mongorunway.tracking.application.ports.auditlog_journal import AuditlogJournal


class TracedMigrationUI(MigrationUI):
    """A migration UI that traces each migration and records it in an auditlog journal.

    Parameters
    ----------
    app: MigrationUI
        The migration UI to be traced.
    auditlog_journal: AuditlogJournal
        The auditlog journal to which the migration traces will be recorded.
    timezone: str, optional
        The timezone to use for timestamps in the auditlog journal. Default is 'UTC'.
    """

    __slots__: typing.Sequence[str] = (
        "_timezone",
        "_application",
        "_auditlog_journal",
    )

    def __init__(
        self,
        app: MigrationUI,
        auditlog_journal: AuditlogJournal,
        timezone: str = "UTC",
    ) -> None:
        self._timezone = timezone
        self._application = app
        self._auditlog_journal = auditlog_journal

    @property
    def name(self) -> str:
        """Return the name of the migration app.

        Returns
        -------
        str
            The name of the migration app.
        """
        return self._application.name

    @property
    def config(self) -> ApplicationConfig:
        """Return the configuration of the migration app.

        Returns
        -------
        ApplicationConfig
            The configuration of the migration app.
        """
        return self._application.config

    @property
    def session(self) -> ApplicationSession:
        """Return the session of the migration app.

        Returns
        -------
        ApplicationSession
            The session of the migration app.
        """
        return self._application.session

    @property
    def pending(self) -> MigrationQueue:
        """Return the pending migrations of the migration app.

        Returns
        -------
        MigrationQueue
            The pending migrations of the migration app.
        """
        return self._application.pending

    @property
    def applied(self) -> MigrationQueue:
        """Return the applied migrations of the migration app.

        Returns
        -------
        MigrationQueue
            The applied migrations of the migration app.
        """
        return self._application.applied

    def append_pending_migration(self, migration: Migration, /) -> None:
        """Append a migration to the list of pending migrations.

        Adds an entry `PendingMigrationAdded` to the audit log journal.

        Parameters
        ----------
        migration : Migration
            The migration to be added to the list of pending migrations.

        Notes
        -----
        If the given migration is already present in either the pending or applied
        migrations list, it will not be added again.
        """
        self._application.append_pending_migration(migration)

        pending_added = PendingMigrationAdded.new(
            migration_read_model=MigrationReadModel.from_migration(
                self._application.pending.acquire_latest_migration(),
            ),
        )

        self._auditlog_journal.append_entry(pending_added.with_time_zone(self._timezone))

    def remove_pending_migration(self, migration_version: int, /) -> None:
        """Remove a pending migration with the given version number.

        Adds an entry `PendingMigrationRemoved` to the audit log journal.

        Parameters
        ----------
        migration_version : int
            The version number of the migration to be removed.

        Notes
        -----
        This method removes a pending migration with the given version number from
        the list of pending migrations. If no migration with the given version number
        is found in the list, this method has no effect.
        """
        migration_to_remove = self._application.pending.acquire_migration(migration_version)

        self._application.remove_pending_migration(migration_version)

        pending_removed = PendingMigrationRemoved.new(
            migration_read_model=MigrationReadModel.from_migration(
                migration_to_remove,
            ),
        )

        self._auditlog_journal.append_entry(pending_removed.with_time_zone(self._timezone))

    def upgrade_once(self) -> int:
        """Apply a single pending migration and commit the changes to the database.

        Adds an entry `MigrationUpgraded` to the audit log journal.

        Returns
        -------
        int
            An integer indicating the success or failure of the upgrade transaction.

        Raises
        ------
        NothingToUpgradeError
            If there are no pending migrations and raise_if_nothing_happens is True in the
            runtime configuration.
        """
        migration_to_upgrade = self._application.pending.acquire_waiting_migration()
        upgraded_count = self._application.upgrade_once()

        migration_upgraded = MigrationUpgraded.new(
            migration_read_model=MigrationReadModel.from_migration(
                migration_to_upgrade,
            ),
            upgraded_count=upgraded_count,
        )

        self._auditlog_journal.append_entry(migration_upgraded.with_time_zone(self._timezone))

        return upgraded_count

    def downgrade_once(self) -> int:
        """Revert the most recently applied migration and commit the changes to the database.

        Adds an entry `MigrationDowngraded` to the audit log journal.

        Returns
        -------
        int
            An integer indicating the success or failure of the downgrade transaction.

        Raises
        ------
        NothingToDowngradeError:
            If there are no applied migrations and `raise_if_nothing_happens` configuration
            parameter is True.
        """
        migration_to_downgrade = self._application.applied.acquire_waiting_migration()
        downgraded_count = self._application.downgrade_once()

        migration_downgraded = MigrationDowngraded.new(
            migration_read_model=MigrationReadModel.from_migration(
                migration_to_downgrade,
            ),
            downgraded_count=downgraded_count,
        )

        self._auditlog_journal.append_entry(migration_downgraded.with_time_zone(self._timezone))

        return downgraded_count

    def upgrade_while(self, predicate: typing.Callable[[Migration], bool], /) -> int:
        """Apply pending migrations until a certain condition is met and commit the
        changes to the database.

        Adds an entry `BulkMigrationUpgraded` to the audit log journal.

        Parameters
        ----------
        predicate : Callable[[Migration], bool]
            A callable object that takes a Migration object as an argument and returns a
            boolean value. The predicate is used to determine when to stop applying migrations.

        Returns
        -------
        int
            The number of migrations that were successfully applied.

        Raises
        ------
        NothingToUpgradeError
            If there are no pending migrations and raise_if_nothing_happens is True in the
            runtime configuration.

        Notes
        -----
        This method applies pending migrations until a certain condition is met.
        """
        migrations_to_upgrade = self._application.pending.acquire_all_migrations()
        upgraded_count = self._application.upgrade_while(predicate)

        self._apply_bulk_upgrade_entry(upgraded_count, migrations_to_upgrade)

        return upgraded_count

    def downgrade_while(self, predicate: typing.Callable[[Migration], bool], /) -> int:
        """Downgrade applied migrations while the given predicate function is true.

        Adds an entry `BulkMigrationDowngraded` to the audit log journal.

        Parameters
        ----------
        predicate : Callable[[Migration], bool]
            A callable object that accepts a single argument of type Migration and
            returns a boolean. This predicate function is used to determine whether
            to continue downgrading the next migration or not.

        Returns
        -------
        int
            The number of migrations that have been downgraded.

        Raises
        ------
        NothingToDowngradeError:
            If there are no applied migrations and `raise_if_nothing_happens` configuration
            parameter is True.

        Notes
        -----
        If the predicate function returns False for a migration, the method stops downgrading
        and returns the number of migrations that have been successfully downgraded.
        """
        migrations_to_downgrade = self._application.applied.acquire_all_migrations()
        downgraded_count = self._application.downgrade_while(predicate)

        self._apply_bulk_downgrade_entry(downgraded_count, migrations_to_downgrade)

        return downgraded_count

    def downgrade_to(self, migration_version: int, /) -> int:
        """Downgrades the database to the specified migration version.

        Adds an entry `BulkMigrationDowngraded` to the audit log journal.

        Parameters
        ----------
        migration_version : int
            The migration version to which the database should be downgraded.

        Returns
        -------
        int
            The number of migrations successfully downgraded.

        Raises
        ------
        NothingToDowngradeError
            If there are no applied migrations and `raise_if_nothing_happens` configuration
            parameter is True.
        ValueError
            If the specified migration version is not found in the applied migrations.

        Notes
        -----
        If the `migration_version` argument is `0`, the method will call `downgrade_all()`
        method which downgrades all applied migrations.
        """
        migrations_to_downgrade = self._application.applied.acquire_all_migrations()
        downgraded_count = self._application.downgrade_to(migration_version)

        self._apply_bulk_downgrade_entry(downgraded_count, migrations_to_downgrade)

        return downgraded_count

    def upgrade_to(self, migration_version: int, /) -> int:
        """Upgrades the database to the specified migration version.

        Adds an entry `BulkMigrationUpgraded` to the audit log journal.

        Parameters
        ----------
        migration_version : int
            The migration version to which the database should be upgraded.

        Returns
        -------
        int
            The number of migrations successfully upgraded.

        Raises
        ------
        NothingToUpgradeError
            If there are no pending migrations and raise_if_nothing_happens is True in the
            runtime configuration.
        ValueError
            If the specified migration version is not found in the pending migrations.
        """
        migrations_to_upgrade = self._application.pending.acquire_all_migrations()
        upgraded_count = self._application.upgrade_to(migration_version)

        self._apply_bulk_upgrade_entry(upgraded_count, migrations_to_upgrade)

        return upgraded_count

    def downgrade_all(self) -> int:
        """Downgrades the database by undoing all previously applied migrations.

        Adds an entry `BulkMigrationDowngraded` to the audit log journal.

        Returns
        -------
        int
            The number of migrations successfully downgraded.

        Raises
        ------
        NothingToDowngradeError
            If there are no applied migrations and `raise_if_nothing_happens` configuration
            parameter is True.
        """
        migrations_to_downgrade = self._application.applied.acquire_all_migrations()
        downgraded_count = self._application.downgrade_all()

        self._apply_bulk_downgrade_entry(downgraded_count, migrations_to_downgrade)

        return downgraded_count

    def upgrade_all(self) -> int:
        """Upgrades the database by applying all pending migrations.

        Adds an entry `BulkMigrationUpgraded` to the audit log journal.

        Returns
        -------
        int
            The number of migrations successfully upgraded.

        Raises
        ------
        NothingToUpgradeError
            If there are no pending migrations and raise_if_nothing_happens is True in the
            runtime configuration.
        """
        migrations_to_upgrade = self._application.pending.acquire_all_migrations()
        upgraded_count = self._application.upgrade_all()

        self._apply_bulk_upgrade_entry(upgraded_count, migrations_to_upgrade)

        return upgraded_count

    def create_migration_file_template(
        self,
        migration_filename: str,
        migration_version: typing.Optional[int] = None,
    ) -> None:
        """Creates a new migration file template with the provided filename and version.

        Parameters
        ----------
        migration_filename : str
            The name of the migration file to be created.
        migration_version : int, optional
            The version number of the migration. If not provided, the next version number
            will be used based on the existing migrations. Defaults to None.

        Raises
        ------
        ValueError
            If a migration with the same version number already exists.
        """
        self._application.create_migration_file_template(migration_filename, migration_version)

    def get_migration_from_filename(self, migration_name: str) -> Migration:
        """Returns a Migration object corresponding to the migration with the given filename.

        Parameters
        ----------
        migration_name : str
            The name of the migration file to retrieve the Migration object for.

        Returns
        -------
        Migration
            A Migration object representing the migration with the given filename.
        """
        return self._application.get_migration_from_filename(migration_name)

    def get_migrations_from_directory(self) -> typing.Sequence[Migration]:
        """Returns a list of Migration objects representing all the migrations in the
        migrations directory.

        Returns
        -------
        Sequence[Migration]
            A list of Migration objects representing all the migrations in the
            migrations directory.

        Raises
        ------
        ValueError
            If the versioning start specified in the configuration is not found in the
            migrations directory.
        ImportError
            If `strict_naming` configuration parameter is False and migration file does
            not contain `version` variable.
        """
        return self._application.get_migrations_from_directory()

    def get_current_version(self) -> typing.Optional[int]:
        """Return the version of the latest applied migration, or None if no migrations
        have been applied yet.

        Returns
        -------
        Optional[int]
            The version of the latest applied migration, or None if no migrations have
            been applied yet.
        """
        return self._application.get_current_version()

    def _apply_bulk_upgrade_entry(
        self, upgraded_count: int, migrations_to_upgrade: typing.Iterable[Migration], /
    ) -> None:
        """Appends an entry to the audit log for a bulk migration upgrade operation.

        Parameters
        ----------
        upgraded_count: int
            The number of migrations that were upgraded.
        migrations_to_upgrade: Iterable[Migration]
            An iterable of the migrations that were upgraded.
        """
        bulk_migration_upgraded = BulkMigrationUpgraded.new(
            upgraded_count=upgraded_count,
            upgraded_migrations=[MigrationReadModel.from_migration(m) for m in migrations_to_upgrade],
        )

        self._auditlog_journal.append_entry(bulk_migration_upgraded.with_time_zone(self._timezone))

    def _apply_bulk_downgrade_entry(
        self, downgraded_count: int, migrations_to_downgrade: typing.Iterable[Migration], /
    ) -> None:
        """Appends an entry to the audit log for a bulk migration downgrade operation.

        Parameters
        ----------
        downgraded_count: int
            The number of migrations that were downgraded.
        migrations_to_downgrade: Iterable[Migration]
            An iterable of the migrations that were downgraded.
        """
        bulk_migration_downgraded = BulkMigrationDowngraded.new(
            downgraded_count=downgraded_count,
            downgraded_migrations=[MigrationReadModel.from_migration(m) for m in migrations_to_downgrade],
        )

        self._auditlog_journal.append_entry(bulk_migration_downgraded.with_time_zone(self._timezone))
