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

from pymongo.database import Database
import pymongo
import pytest

from mongorunway.kernel.persistence.queues import (
    BaseMigrationQueue,
    PendingMigrationQueue,
    AppliedMigrationQueue,
)

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration import Migration
    from mongorunway.kernel.application.ui import MigrationUI
    from mongorunway.kernel.application.ports.queue import MigrationQueue


class TestBaseMigrationQueue:
    @pytest.fixture
    def queue(
        self,
        application: MigrationUI,
        mongodb: Database[typing.Dict[str, typing.Any]],
    ) -> MigrationQueue:
        return BaseMigrationQueue(
            application,
            sort_order=pymongo.ASCENDING,  # doesn't matter
            collection=mongodb.pending_migrations,
        )

    def test_queue_len(self, queue: MigrationQueue, migration: Migration) -> None:
        assert len(queue) == 0

        queue.append_migration(migration)
        assert len(queue) > 0

    def test_queue_contains(self, queue: MigrationQueue, migration: Migration) -> None:
        assert migration not in queue

        queue.append_migration(migration)
        assert migration in queue

    def test_queue_has_migration(self, queue: MigrationQueue, migration: Migration) -> None:
        with pytest.raises(TypeError):
            assert not queue.has_migration(1)

        assert migration not in queue

        queue.append_migration(migration)
        assert queue.has_migration(migration)

    def test_queue_has_migration_with_version(self, queue: MigrationQueue, migration: Migration) -> None:
        with pytest.raises(TypeError):
            assert not queue.has_migration_with_version(migration)

        assert migration not in queue

        queue.append_migration(migration)
        assert queue.has_migration_with_version(migration.version)

    def test_queue_has_migrations(self, queue: MigrationQueue, migration: Migration) -> None:
        assert not queue.has_migrations()

        queue.append_migration(migration)
        assert queue.has_migrations()

    def test_queue_remove_migration(self, queue: MigrationQueue, migration: Migration) -> None:
        assert not queue.has_migrations()

        queue.append_migration(migration)
        assert queue.has_migrations()

        with pytest.raises(TypeError):
            queue.remove_migration(migration)

        queue.remove_migration(migration.version)
        assert not queue.has_migrations()

    def test_queue_acquire_migration(
        self, queue: MigrationQueue, application: MigrationUI, migration: Migration, tmp_path: pathlib.Path,
    ) -> None:
        assert not queue.has_migrations()

        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)

        queue.append_migration(migration)
        acquired_migration = queue.acquire_migration(migration.version)

        assert acquired_migration.version == migration.version
        assert acquired_migration.name == migration.name

        # Template does not have commands by default
        assert not acquired_migration.downgrade_commands
        assert not acquired_migration.upgrade_commands

    def test_queue_acquire_waiting_migration(
        self, queue: MigrationQueue, application: MigrationUI, migration: Migration, tmp_path: pathlib.Path,
    ) -> None:
        assert not queue.has_migrations()

        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)

        queue.append_migration(migration)
        acquired_migration = queue.acquire_waiting_migration()

        assert acquired_migration.version == migration.version
        assert acquired_migration.name == migration.name

        # Template does not have commands by default
        assert not acquired_migration.downgrade_commands
        assert not acquired_migration.upgrade_commands

    def test_queue_pop_waiting_migration(
        self, queue: MigrationQueue, application: MigrationUI, migration: Migration, tmp_path: pathlib.Path,
    ) -> None:
        assert not queue.has_migrations()

        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)

        queue.append_migration(migration)
        assert queue.has_migrations()

        acquired_migration = queue.pop_waiting_migration()
        assert not queue.has_migrations()

        assert acquired_migration.version == migration.version
        assert acquired_migration.name == migration.name

        # Template does not have commands by default
        assert not acquired_migration.downgrade_commands
        assert not acquired_migration.upgrade_commands

    def test_queue_acquire_latest_migration(
        self,
        queue: MigrationQueue,
        application: MigrationUI,
        migration: Migration,
        migration2: Migration,
        tmp_path: pathlib.Path,
    ) -> None:
        assert not queue.has_migrations()

        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)
        application.create_migration_file_template(migration2.name, migration2.version)

        queue.append_migration(migration)
        queue.append_migration(migration2)
        assert queue.has_migrations()

        acquired_migration = queue.acquire_latest_migration()

        assert acquired_migration.version == migration2.version
        assert acquired_migration.name == migration2.name

        # Template does not have commands by default
        assert not acquired_migration.downgrade_commands
        assert not acquired_migration.upgrade_commands

    def test_queue_acquire_first_migration(
        self,
        queue: MigrationQueue,
        application: MigrationUI,
        migration: Migration,
        migration2: Migration,
        tmp_path: pathlib.Path,
    ) -> None:
        assert not queue.has_migrations()

        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)
        application.create_migration_file_template(migration2.name, migration2.version)

        queue.append_migration(migration)
        queue.append_migration(migration2)
        assert queue.has_migrations()

        acquired_migration = queue.acquire_first_migration()

        assert acquired_migration.version == migration.version
        assert acquired_migration.name == migration.name

        # Template does not have commands by default
        assert not acquired_migration.downgrade_commands
        assert not acquired_migration.upgrade_commands

    def test_queue_acquire_all_migrations(
        self,
        queue: MigrationQueue,
        application: MigrationUI,
        migration: Migration,
        migration2: Migration,
        tmp_path: pathlib.Path,
    ) -> None:
        assert not queue.has_migrations()

        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)
        application.create_migration_file_template(migration2.name, migration2.version)

        queue.append_migration(migration)
        queue.append_migration(migration2)
        assert queue.has_migrations()

        # Assertion for sorting order tests
        assert migration.version < migration2.version

        # Sorting by ascending versions
        acquired_migrations = queue.acquire_all_migrations(sort_by=pymongo.ASCENDING)
        assert acquired_migrations[0].version == migration.version

        # Sorting by descending versions
        acquired_migrations = queue.acquire_all_migrations(sort_by=pymongo.DESCENDING)
        assert acquired_migrations[0].version == migration2.version


class TestAppliedMigrationQueue:  # LIFO
    @pytest.fixture
    def queue(
        self,
        application: MigrationUI,
        mongodb: Database[typing.Dict[str, typing.Any]],
    ) -> MigrationQueue:
        return AppliedMigrationQueue(application)

    def test_queue_acquire_waiting_migration(
        self,
        queue: MigrationQueue,
        application: MigrationUI,
        migration: Migration,
        migration2: Migration,
        tmp_path: pathlib.Path,
    ) -> None:
        assert not queue.has_migrations()

        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)
        application.create_migration_file_template(migration2.name, migration2.version)

        queue.append_migration(migration)
        queue.append_migration(migration2)

        # Last in, first out
        acquired_migration = queue.acquire_waiting_migration()

        assert acquired_migration.version == migration2.version
        assert acquired_migration.name == migration2.name

        # Template does not have commands by default
        assert not acquired_migration.downgrade_commands
        assert not acquired_migration.upgrade_commands

    def test_queue_pop_waiting_migration(
        self,
        queue: MigrationQueue,
        application: MigrationUI,
        migration: Migration,
        migration2: Migration,
        tmp_path: pathlib.Path,
    ) -> None:
        assert not queue.has_migrations()

        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)
        application.create_migration_file_template(migration2.name, migration2.version)

        queue.append_migration(migration)
        queue.append_migration(migration2)
        assert len(queue) == 2

        # Last in, first out
        acquired_migration = queue.pop_waiting_migration()
        assert len(queue) == 1

        assert acquired_migration.version == migration2.version
        assert acquired_migration.name == migration2.name

        # Template does not have commands by default
        assert not acquired_migration.downgrade_commands
        assert not acquired_migration.upgrade_commands


class TestPendingMigrationQueue:  # FIFO
    @pytest.fixture
    def queue(
        self,
        application: MigrationUI,
        mongodb: Database[typing.Dict[str, typing.Any]],
    ) -> MigrationQueue:
        return PendingMigrationQueue(application)

    def test_queue_acquire_waiting_migration(
        self,
        queue: MigrationQueue,
        application: MigrationUI,
        migration: Migration,
        migration2: Migration,
        tmp_path: pathlib.Path,
    ) -> None:
        assert not queue.has_migrations()

        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)
        application.create_migration_file_template(migration2.name, migration2.version)

        queue.append_migration(migration)
        queue.append_migration(migration2)

        # First in, first out
        acquired_migration = queue.acquire_waiting_migration()

        assert acquired_migration.version == migration.version
        assert acquired_migration.name == migration.name

        # Template does not have commands by default
        assert not acquired_migration.downgrade_commands
        assert not acquired_migration.upgrade_commands

    def test_queue_pop_waiting_migration(
        self,
        queue: MigrationQueue,
        application: MigrationUI,
        migration: Migration,
        migration2: Migration,
        tmp_path: pathlib.Path,
    ) -> None:
        assert not queue.has_migrations()

        # Reloading temp migrations dir
        application.config.migration_scripts_dir = str(tmp_path)
        application.create_migration_file_template(migration.name, migration.version)
        application.create_migration_file_template(migration2.name, migration2.version)

        queue.append_migration(migration)
        queue.append_migration(migration2)
        assert len(queue) == 2

        # First in, first out
        acquired_migration = queue.pop_waiting_migration()
        assert len(queue) == 1

        assert acquired_migration.version == migration.version
        assert acquired_migration.name == migration.name

        # Template does not have commands by default
        assert not acquired_migration.downgrade_commands
        assert not acquired_migration.upgrade_commands
