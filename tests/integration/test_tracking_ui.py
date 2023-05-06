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
from __future__ import annotations

import pathlib
import typing

import pytest

from mongorunway.tracking.application.ui import TracedMigrationUI
from mongorunway.tracking.persistence.auditlog_journals import BaseAuditlogJournal
from mongorunway.tracking.domain.auditlog_entry import (
    MigrationUpgraded,
    MigrationDowngraded,
    PendingMigrationAdded,
    PendingMigrationRemoved,
    BulkMigrationUpgraded,
    BulkMigrationDowngraded,
)
from mongorunway.kernel.domain.migration import Migration

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.ui import MigrationUI


class TestTracedMigrationUI:
    @pytest.fixture(scope="function")
    def base_auditlog_journal(self, application: MigrationUI) -> BaseAuditlogJournal:
        return BaseAuditlogJournal(application.config.auditlog.auditlog_collection)

    @pytest.fixture(scope="function")
    def traced_migration_app(
        self, application: MigrationUI, base_auditlog_journal: BaseAuditlogJournal,
    ) -> TracedMigrationUI:
        return TracedMigrationUI(application, base_auditlog_journal)

    def test_assert_initialized_correctly(
        self, traced_migration_app: TracedMigrationUI, application: MigrationUI
    ) -> None:
        assert traced_migration_app.name == application.name
        assert traced_migration_app.config == application.config
        assert traced_migration_app.session == application.session
        assert traced_migration_app.pending == application.pending
        assert traced_migration_app.applied == application.applied

    def test_append_pending_migration(
        self,
        traced_migration_app: TracedMigrationUI,
        migration: Migration,
        base_auditlog_journal: BaseAuditlogJournal,
        tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        traced_migration_app.config.migration_scripts_dir = str(tmp_path)
        traced_migration_app.create_migration_file_template(migration.name, migration.version)

        assert len(base_auditlog_journal.load_entries()) == 0

        traced_migration_app.append_pending_migration(migration)
        entries = base_auditlog_journal.load_entries()
        assert len(entries) == 1

        assert isinstance(entries[0], PendingMigrationAdded)

    def test_remove_pending_migration(
        self,
        traced_migration_app: TracedMigrationUI,
        migration: Migration,
        base_auditlog_journal: BaseAuditlogJournal,
        tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        traced_migration_app.config.migration_scripts_dir = str(tmp_path)
        traced_migration_app.create_migration_file_template(migration.name, migration.version)

        # Setting up environment
        traced_migration_app._application.append_pending_migration(migration)

        assert len(base_auditlog_journal.load_entries()) == 0

        traced_migration_app.remove_pending_migration(migration.version)
        entries = base_auditlog_journal.load_entries()
        assert len(entries) == 1

        assert isinstance(entries[0], PendingMigrationRemoved)

    def test_upgrade_once(
        self,
        traced_migration_app: TracedMigrationUI,
        migration: Migration,
        base_auditlog_journal: BaseAuditlogJournal,
        tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        traced_migration_app.config.migration_scripts_dir = str(tmp_path)
        traced_migration_app.create_migration_file_template(migration.name, migration.version)

        # Setting up environment
        traced_migration_app._application.append_pending_migration(migration)

        assert len(base_auditlog_journal.load_entries()) == 0

        traced_migration_app.upgrade_once()
        entries = base_auditlog_journal.load_entries()
        assert len(entries) == 1

        assert isinstance(entries[0], MigrationUpgraded)

    def test_downgrade_once(
        self,
        traced_migration_app: TracedMigrationUI,
        migration: Migration,
        base_auditlog_journal: BaseAuditlogJournal,
        tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        traced_migration_app.config.migration_scripts_dir = str(tmp_path)
        traced_migration_app.create_migration_file_template(migration.name, migration.version)

        # Setting up environment
        traced_migration_app._application.applied.append_migration(migration)

        assert len(base_auditlog_journal.load_entries()) == 0

        traced_migration_app.downgrade_once()
        entries = base_auditlog_journal.load_entries()
        assert len(entries) == 1

        assert isinstance(entries[0], MigrationDowngraded)

    def test_upgrade_while(
        self,
        traced_migration_app: TracedMigrationUI,
        migration: Migration,
        base_auditlog_journal: BaseAuditlogJournal,
        tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        traced_migration_app.config.migration_scripts_dir = str(tmp_path)
        traced_migration_app.create_migration_file_template(migration.name, migration.version)

        # Setting up environment
        traced_migration_app._application.append_pending_migration(migration)

        assert len(base_auditlog_journal.load_entries()) == 0

        traced_migration_app.upgrade_while(lambda m: True)
        entries = base_auditlog_journal.load_entries()
        assert len(entries) == 1

        assert isinstance(entries[0], BulkMigrationUpgraded)

    def test_upgrade_to(
        self,
        traced_migration_app: TracedMigrationUI,
        migration: Migration,
        base_auditlog_journal: BaseAuditlogJournal,
        tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        traced_migration_app.config.migration_scripts_dir = str(tmp_path)
        traced_migration_app.create_migration_file_template(migration.name, migration.version)

        # Setting up environment
        traced_migration_app._application.append_pending_migration(migration)

        assert len(base_auditlog_journal.load_entries()) == 0

        traced_migration_app.upgrade_to(1)
        entries = base_auditlog_journal.load_entries()
        assert len(entries) == 1

        assert isinstance(entries[0], BulkMigrationUpgraded)

    def test_upgrade_all(
        self,
        traced_migration_app: TracedMigrationUI,
        migration: Migration,
        base_auditlog_journal: BaseAuditlogJournal,
        tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        traced_migration_app.config.migration_scripts_dir = str(tmp_path)
        traced_migration_app.create_migration_file_template(migration.name, migration.version)

        # Setting up environment
        traced_migration_app._application.append_pending_migration(migration)

        assert len(base_auditlog_journal.load_entries()) == 0

        traced_migration_app.upgrade_all()
        entries = base_auditlog_journal.load_entries()
        assert len(entries) == 1

        assert isinstance(entries[0], BulkMigrationUpgraded)

    def test_downgrade_while(
        self,
        traced_migration_app: TracedMigrationUI,
        migration: Migration,
        base_auditlog_journal: BaseAuditlogJournal,
        tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        traced_migration_app.config.migration_scripts_dir = str(tmp_path)
        traced_migration_app.create_migration_file_template(migration.name, migration.version)

        # Setting up environment
        traced_migration_app._application.applied.append_migration(migration)

        assert len(base_auditlog_journal.load_entries()) == 0

        traced_migration_app.downgrade_while(lambda m: True)
        entries = base_auditlog_journal.load_entries()
        assert len(entries) == 1

        assert isinstance(entries[0], BulkMigrationDowngraded)

    def test_downgrade_to(
        self,
        traced_migration_app: TracedMigrationUI,
        migration: Migration,
        base_auditlog_journal: BaseAuditlogJournal,
        tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        traced_migration_app.config.migration_scripts_dir = str(tmp_path)
        traced_migration_app.create_migration_file_template(migration.name, migration.version)

        # Setting up environment
        traced_migration_app._application.applied.append_migration(migration)

        assert len(base_auditlog_journal.load_entries()) == 0

        traced_migration_app.downgrade_to(0)
        entries = base_auditlog_journal.load_entries()
        assert len(entries) == 1

        assert isinstance(entries[0], BulkMigrationDowngraded)

    def test_downgrade_all(
        self,
        traced_migration_app: TracedMigrationUI,
        migration: Migration,
        base_auditlog_journal: BaseAuditlogJournal,
        tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        traced_migration_app.config.migration_scripts_dir = str(tmp_path)
        traced_migration_app.create_migration_file_template(migration.name, migration.version)

        # Setting up environment
        traced_migration_app._application.applied.append_migration(migration)

        assert len(base_auditlog_journal.load_entries()) == 0

        traced_migration_app.downgrade_all()
        entries = base_auditlog_journal.load_entries()
        assert len(entries) == 1

        assert isinstance(entries[0], BulkMigrationDowngraded)

    def test_create_migration_file_template(
        self,
        traced_migration_app: TracedMigrationUI,
        migration: Migration,
        migration2: Migration,
        tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        traced_migration_app.config.migration_scripts_dir = str(tmp_path)

        traced_migration_app.create_migration_file_template(migration.name, migration.version)
        migration_from_file = traced_migration_app.get_migration_from_filename(migration.name)
        assert isinstance(migration_from_file, Migration)

        # Version autoinc
        traced_migration_app.create_migration_file_template(migration2.name)
        assert traced_migration_app.get_migration_from_filename(migration2.name).version == 2

        traced_migration_app.append_pending_migration(migration)
        with pytest.raises(ValueError):
            # Migration already exist
            traced_migration_app.create_migration_file_template(migration.name, migration.version)

    def test_get_migration_from_filename(
        self,
        traced_migration_app: TracedMigrationUI,
        migration: Migration,
        tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        traced_migration_app.config.migration_scripts_dir = str(tmp_path)

        traced_migration_app.create_migration_file_template(migration.name, migration.version)
        migration_from_file = traced_migration_app.get_migration_from_filename(migration.name)
        assert isinstance(migration_from_file, Migration)

    def test_get_migrations_from_directory(
        self,
        traced_migration_app: TracedMigrationUI,
        migration: Migration,
        migration2: Migration,
        tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        traced_migration_app.config.migration_scripts_dir = str(tmp_path)

        assert len(traced_migration_app.get_migrations_from_directory()) == 0

        traced_migration_app.create_migration_file_template(migration.name, migration.version)
        traced_migration_app.create_migration_file_template(migration2.name, migration2.version)

        assert len(traced_migration_app.get_migrations_from_directory()) == 2

    def test_get_current_version(
        self,
        traced_migration_app: TracedMigrationUI,
        migration: Migration,
        tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        traced_migration_app.config.migration_scripts_dir = str(tmp_path)

        assert traced_migration_app.get_current_version() is None

        traced_migration_app.create_migration_file_template(migration.name, migration.version)
        traced_migration_app.applied.append_migration(migration)
        assert traced_migration_app.get_current_version() == 1
