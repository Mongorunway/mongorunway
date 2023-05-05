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
from unittest import mock

import pytest

from mongorunway.kernel.domain.migration_exception import NothingToUpgradeError, NothingToDowngradeError, MigrationTransactionFailedError
from mongorunway.kernel.application.transactions import TRANSACTION_SUCCESS, TRANSACTION_NOT_APPLIED
from mongorunway.kernel.application.ui import requires_pending_migration, requires_applied_migration, ApplicationSession
from mongorunway.kernel.application.transactions import MigrationTransaction
from mongorunway.kernel.application.ports.hook import MigrationHook, PrioritizedMigrationHook
from mongorunway.kernel.persistence.queues import AppliedMigrationQueue, PendingMigrationQueue
from mongorunway.kernel.application.config import ApplicationConfig
from mongorunway.kernel.domain.migration import Migration
from mongorunway.kernel.application.ui import MigrationUI


def test_requires_pending_migration_decorator(application: MigrationUI, migration: Migration) -> None:
    @requires_pending_migration
    def fake_method(self: MigrationUI) -> int:
        return TRANSACTION_SUCCESS

    with pytest.raises(NothingToUpgradeError):
        # Application does not have migrations by default
        fake_method(application)

    # Config integration
    application.config.runtime.raise_if_nothing_happens = False
    assert fake_method(application) == TRANSACTION_NOT_APPLIED

    application.pending.append_migration(migration)
    assert fake_method(application) == TRANSACTION_SUCCESS


def test_requires_applied_migration_decorator(application: MigrationUI, migration: Migration) -> None:
    @requires_applied_migration
    def fake_method(self: MigrationUI) -> int:
        return TRANSACTION_SUCCESS

    with pytest.raises(NothingToDowngradeError):
        # Application does not have migrations by default
        fake_method(application)

    # Config integration
    application.config.runtime.raise_if_nothing_happens = False
    assert fake_method(application) == TRANSACTION_NOT_APPLIED

    application.applied.append_migration(migration)
    assert fake_method(application) == TRANSACTION_SUCCESS


class TestApplicationSession:
    def test_trigger_hooks(self, application: MigrationUI) -> None:
        base_hooks = [mock.Mock(spec=MigrationHook)]
        prioritized_hooks = [mock.Mock(spec=PrioritizedMigrationHook)]

        with mock.patch.object(
            ApplicationSession, "_apply_hooks", autospec=True
        ) as mock_apply_hooks:
            session = ApplicationSession(application)
            session.trigger_hooks(base_hooks)

            mock_apply_hooks.assert_called_once_with(session, base_hooks)

        with mock.patch.object(
            ApplicationSession, "_apply_prioritized_hooks", autospec=True
        ) as mock_apply_hooks:
            session = ApplicationSession(application)
            session.trigger_hooks(prioritized_hooks)

            mock_apply_hooks.assert_called_once_with(session, prioritized_hooks)

    def test_start_transaction_commit(self, application: MigrationUI) -> None:
        transaction = mock.MagicMock(spec=MigrationTransaction)

        with application.session.start_transaction(transaction) as t:
            assert transaction == t

        transaction.commit.assert_called_once()

    def test_start_transaction_rollback(self, application: MigrationUI) -> None:
        transaction = mock.MagicMock(spec=MigrationTransaction)
        error = ValueError("Some error")
        transaction.commit.side_effect = error

        with pytest.raises(MigrationTransactionFailedError):
            with application.session.start_transaction(transaction):
                pass


class TestMigrationUI:
    def test_ui_correctly_initialized(self, application: MigrationUI) -> None:
        assert application.name == application.config.name
        assert isinstance(application.pending, PendingMigrationQueue)
        assert isinstance(application.applied, AppliedMigrationQueue)
        assert isinstance(application.config, ApplicationConfig)
        assert isinstance(application.session, ApplicationSession)

    def test_append_pending_migration(self, application: MigrationUI, migration: Migration) -> None:
        assert len(application.pending) == 0

        application.append_pending_migration(migration)

        assert len(application.pending) == 1

    def test_remove_pending_migration(self, application: MigrationUI, migration: Migration) -> None:
        assert len(application.pending) == 0

        application.append_pending_migration(migration)
        assert len(application.pending) == 1

        application.remove_pending_migration(migration.version)
        assert len(application.pending) == 0

    def test_upgrade_once(
        self, application: MigrationUI, migration: Migration, tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)

        assert len(application.pending) == 0

        application.append_pending_migration(migration)
        assert len(application.pending) == 1

        assert application.upgrade_once() == TRANSACTION_SUCCESS
        assert len(application.pending) == 0
        assert len(application.applied) == 1

    def test_upgrade_while(
        self, application: MigrationUI, migration: Migration, migration2: Migration, tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)
        application.create_migration_file_template(migration2.name, migration2.version)

        assert len(application.pending) == 0

        application.append_pending_migration(migration)
        application.append_pending_migration(migration2)
        assert len(application.pending) == 2

        assert application.upgrade_while(lambda m: m.version < 2) == 1

        # Applied only one migration
        assert len(application.applied) == 1
        assert len(application.pending) == 1

    def test_upgrade_to(
        self, application: MigrationUI, migration: Migration, migration2: Migration, tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)
        application.create_migration_file_template(migration2.name, migration2.version)

        assert len(application.pending) == 0

        application.append_pending_migration(migration)
        application.append_pending_migration(migration2)
        assert len(application.pending) == 2

        assert application.upgrade_to(1) == 1

        # Applied only one migration
        assert len(application.applied) == 1
        assert len(application.pending) == 1

    def test_upgrade_all(
        self, application: MigrationUI, migration: Migration, migration2: Migration, tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)
        application.create_migration_file_template(migration2.name, migration2.version)

        assert len(application.pending) == 0

        application.append_pending_migration(migration)
        application.append_pending_migration(migration2)
        assert len(application.pending) == 2

        assert application.upgrade_all() == 2

        # All migrations upgraded
        assert len(application.applied) == 2
        assert len(application.pending) == 0

    def test_downgrade_once(
        self, application: MigrationUI, migration: Migration, tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)

        assert len(application.pending) == 0

        application.append_pending_migration(migration)
        assert len(application.pending) == 1

        assert application.upgrade_once() == TRANSACTION_SUCCESS
        assert len(application.pending) == 0
        assert len(application.applied) == 1

        assert application.downgrade_once() == TRANSACTION_SUCCESS
        assert len(application.pending) == 1
        assert len(application.applied) == 0

    def test_downgrade_while(
        self, application: MigrationUI, migration: Migration, migration2: Migration, tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)
        application.create_migration_file_template(migration2.name, migration2.version)

        assert len(application.applied) == 0

        application.applied.append_migration(migration)
        application.applied.append_migration(migration2)
        assert len(application.applied) == 2

        assert application.downgrade_while(lambda m: m.version == 2) == 1

        # Applied only one migration
        assert len(application.applied) == 1
        assert len(application.pending) == 1

    def test_downgrade_all(
        self, application: MigrationUI, migration: Migration, migration2: Migration, tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)
        application.create_migration_file_template(migration2.name, migration2.version)

        assert len(application.applied) == 0

        application.applied.append_migration(migration)
        application.applied.append_migration(migration2)
        assert len(application.applied) == 2

        assert application.downgrade_all() == 2

        # All migrations downgraded
        assert len(application.applied) == 0
        assert len(application.pending) == 2

    def test_downgrade_to(
        self, application: MigrationUI, migration: Migration, migration2: Migration, tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)
        application.create_migration_file_template(migration2.name, migration2.version)

        assert len(application.applied) == 0

        application.applied.append_migration(migration)
        application.applied.append_migration(migration2)
        assert len(application.applied) == 2

        assert application.downgrade_to(1) == 1

        # Applied only one migration
        assert len(application.applied) == 1
        assert len(application.pending) == 1

    def test_create_migration_file_template(
        self, application: MigrationUI, migration: Migration, migration2: Migration, tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)

        application.create_migration_file_template(migration.name, migration.version)
        migration_from_file = application.get_migration_from_filename(migration.name)
        assert isinstance(migration_from_file, Migration)

        # Version autoinc
        application.create_migration_file_template(migration2.name)
        assert application.get_migration_from_filename(migration2.name).version == 2

        application.append_pending_migration(migration)
        with pytest.raises(ValueError):
            # Migration already exist
            application.create_migration_file_template(migration.name, migration.version)

    def test_get_migration_from_filename(
        self, application: MigrationUI, migration: Migration, tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)

        application.create_migration_file_template(migration.name, migration.version)
        migration_from_file = application.get_migration_from_filename(migration.name)
        assert isinstance(migration_from_file, Migration)

    def test_get_migrations_from_directory(
        self, application: MigrationUI, migration: Migration, migration2: Migration, tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)

        assert len(application.get_migrations_from_directory()) == 0

        application.create_migration_file_template(migration.name, migration.version)
        application.create_migration_file_template(migration2.name, migration2.version)

        assert len(application.get_migrations_from_directory()) == 2

    def test_get_current_version(
        self, application: MigrationUI, migration: Migration, tmp_path: pathlib.Path,
    ) -> None:
        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)

        assert application.get_current_version() is None

        application.create_migration_file_template(migration.name, migration.version)
        application.applied.append_migration(migration)
        assert application.get_current_version() == 1
