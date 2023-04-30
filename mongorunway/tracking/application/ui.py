from __future__ import annotations

__all__: typing.Sequence[str] = ("TracedMigrationUI",)

import typing

from mongorunway.kernel.application.ui import MigrationUI
from mongorunway.kernel.domain.migration import MigrationReadModel
from mongorunway.tracking.domain.auditlog_entry import (
    BulkMigrationDowngraded,
    BulkMigrationUpgraded,
    MigrationDowngraded,
    MigrationFileTemplateCreated,
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
        return self._application.name

    @property
    def config(self) -> ApplicationConfig:
        return self._application.config

    @property
    def session(self) -> ApplicationSession:
        return self._application.session

    @property
    def pending(self) -> MigrationQueue:
        return self._application.pending

    @property
    def applied(self) -> MigrationQueue:
        return self._application.applied

    def append_pending_migration(self, migration: Migration, /) -> None:
        self._application.append_pending_migration(migration)

        pending_added = PendingMigrationAdded.new(
            migration_read_model=MigrationReadModel.from_migration(
                self._application.pending.acquire_latest_migration(),
            ),
        )

        self._auditlog_journal.append_entry(pending_added.with_time_zone(self._timezone))

    def remove_pending_migration(self, migration_version: int, /) -> None:
        migration_to_remove = self._application.pending.acquire_migration(migration_version)

        self._application.remove_pending_migration(migration_version)

        pending_removed = PendingMigrationRemoved.new(
            migration_read_model=MigrationReadModel.from_migration(
                migration_to_remove,
            ),
        )

        self._auditlog_journal.append_entry(pending_removed.with_time_zone(self._timezone))

    def upgrade_once(self) -> int:
        migration_to_upgrade = self._application.pending.acquire_nowait_migration()
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
        migration_to_downgrade = self._application.applied.acquire_nowait_migration()
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
        migrations_to_upgrade = self._application.pending.acquire_all_migrations()
        upgraded_count = self._application.upgrade_while(predicate)

        self._apply_bulk_upgrade_entry(upgraded_count, migrations_to_upgrade)

        return upgraded_count

    def downgrade_while(self, predicate: typing.Callable[[Migration], bool], /) -> int:
        migrations_to_downgrade = self._application.applied.acquire_all_migrations()
        downgraded_count = self._application.upgrade_while(predicate)

        self._apply_bulk_downgrade_entry(downgraded_count, migrations_to_downgrade)

        return downgraded_count

    def downgrade_to(self, migration_version: int, /) -> int:
        migrations_to_downgrade = self._application.applied.acquire_all_migrations()
        downgraded_count = self._application.downgrade_to(migration_version)

        self._apply_bulk_downgrade_entry(downgraded_count, migrations_to_downgrade)

        return downgraded_count

    def upgrade_to(self, migration_version: int, /) -> int:
        migrations_to_upgrade = self._application.pending.acquire_all_migrations()
        upgraded_count = self._application.upgrade_to(migration_version)

        self._apply_bulk_upgrade_entry(upgraded_count, migrations_to_upgrade)

        return upgraded_count

    def downgrade_all(self) -> int:
        migrations_to_downgrade = self._application.applied.acquire_all_migrations()
        downgraded_count = self._application.downgrade_all()

        self._apply_bulk_downgrade_entry(downgraded_count, migrations_to_downgrade)

        return downgraded_count

    def upgrade_all(self) -> int:
        migrations_to_upgrade = self._application.pending.acquire_all_migrations()
        upgraded_count = self._application.upgrade_all()

        self._apply_bulk_upgrade_entry(upgraded_count, migrations_to_upgrade)

        return upgraded_count

    def create_migration_file_template(
        self,
        migration_filename: str,
        migration_version: typing.Optional[int] = None,
    ) -> None:
        migration_file_template_created = MigrationFileTemplateCreated.new(
            migration_filename=migration_filename,
            migration_version=migration_version,
        )

        self._auditlog_journal.append_entry(migration_file_template_created.with_time_zone(self._timezone))

    def get_migration_from_filename(self, migration_name: str) -> Migration:
        return self._application.get_migration_from_filename(migration_name)

    def get_migrations_from_directory(self) -> typing.Sequence[Migration]:
        return self._application.get_migrations_from_directory()

    def get_current_version(self) -> typing.Optional[int]:
        return self._application.get_current_version()

    def _apply_bulk_upgrade_entry(
        self, upgraded_count: int, migrations_to_upgrade: typing.Iterable[Migration], /
    ) -> None:
        bulk_migration_upgraded = BulkMigrationUpgraded.new(
            upgraded_count=upgraded_count,
            upgraded_migrations=[MigrationReadModel.from_migration(m) for m in migrations_to_upgrade],
        )

        self._auditlog_journal.append_entry(bulk_migration_upgraded.with_time_zone(self._timezone))

    def _apply_bulk_downgrade_entry(
        self, downgraded_count: int, migrations_to_downgrade: typing.Iterable[Migration], /
    ) -> None:
        bulk_migration_downgraded = BulkMigrationDowngraded.new(
            downgraded_count=downgraded_count,
            downgraded_migrations=[MigrationReadModel.from_migration(m) for m in migrations_to_downgrade],
        )

        self._auditlog_journal.append_entry(bulk_migration_downgraded.with_time_zone(self._timezone))
