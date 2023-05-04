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

import pymongo
import pytest

from mongorunway.kernel.application.services.query_service import MigrationQueryService

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration import Migration
    from mongorunway.kernel.application.ui import MigrationUI


@pytest.fixture(scope="function")
def query_service(application: MigrationUI) -> MigrationQueryService:
    return MigrationQueryService(application)


def test_get_pending_migrations(
    application: MigrationUI,
    query_service: MigrationQueryService,
    migration: Migration,
    migration2: Migration,
    tmp_path: pathlib.Path,
) -> None:
    # Reloading temp migrations dir
    application.config.migration_scripts_dir = str(tmp_path)

    assert len(query_service.get_pending_migrations()) == 0

    application.create_migration_file_template(migration.name, migration.version)
    application.pending.append_migration(migration)

    assert len(query_service.get_pending_migrations()) == 1

    application.create_migration_file_template(migration2.name, migration2.version)
    application.pending.append_migration(migration2)

    assert len(query_service.get_pending_migrations()) == 2
    assert [m.version for m in query_service.get_pending_migrations(sort_by=pymongo.ASCENDING)] == [1, 2]
    assert [m.version for m in query_service.get_pending_migrations(sort_by=pymongo.DESCENDING)] == [2, 1]


def test_get_pending_migrations_count(
    application: MigrationUI,
    query_service: MigrationQueryService,
    migration: Migration,
    tmp_path: pathlib.Path,
) -> None:
    # Reloading temp migrations dir
    application.config.migration_scripts_dir = str(tmp_path)

    assert query_service.get_pending_migrations_count() == 0

    application.create_migration_file_template(migration.name, migration.version)
    application.pending.append_migration(migration)

    assert query_service.get_pending_migrations_count() == 1


def test_get_first_pending_migration(
    application: MigrationUI,
    query_service: MigrationQueryService,
    migration: Migration,
    migration2: Migration,
    tmp_path: pathlib.Path,
) -> None:
    # Reloading temp migrations dir
    application.config.migration_scripts_dir = str(tmp_path)

    assert query_service.get_first_pending_migration() is None

    application.create_migration_file_template(migration.name, migration.version)
    application.pending.append_migration(migration)

    assert query_service.get_first_pending_migration().version == 1

    application.create_migration_file_template(migration2.name, migration2.version)
    application.pending.append_migration(migration2)

    assert query_service.get_first_pending_migration().version == 1


def test_get_latest_pending_migration(
    application: MigrationUI,
    query_service: MigrationQueryService,
    migration: Migration,
    migration2: Migration,
    tmp_path: pathlib.Path,
) -> None:
    # Reloading temp migrations dir
    application.config.migration_scripts_dir = str(tmp_path)

    assert query_service.get_latest_pending_migration() is None

    application.create_migration_file_template(migration.name, migration.version)
    application.pending.append_migration(migration)

    assert query_service.get_latest_pending_migration().version == 1

    application.create_migration_file_template(migration2.name, migration2.version)
    application.pending.append_migration(migration2)

    assert query_service.get_latest_pending_migration().version == 2


def test_get_pending_waiting_migration_FIFO(
    application: MigrationUI,
    query_service: MigrationQueryService,
    migration: Migration,
    migration2: Migration,
    tmp_path: pathlib.Path,
) -> None:
    # Reloading temp migrations dir
    application.config.migration_scripts_dir = str(tmp_path)

    assert query_service.get_pending_waiting_migration() is None

    application.create_migration_file_template(migration.name, migration.version)
    application.pending.append_migration(migration)

    assert query_service.get_pending_waiting_migration().version == 1

    application.create_migration_file_template(migration2.name, migration2.version)
    application.pending.append_migration(migration2)

    assert query_service.get_pending_waiting_migration().version == 1


def test_get_applied_migrations(
    application: MigrationUI,
    query_service: MigrationQueryService,
    migration: Migration,
    migration2: Migration,
    tmp_path: pathlib.Path,
) -> None:
    # Reloading temp migrations dir
    application.config.migration_scripts_dir = str(tmp_path)

    assert len(query_service.get_applied_migrations()) == 0

    application.create_migration_file_template(migration.name, migration.version)
    application.applied.append_migration(migration)

    assert len(query_service.get_applied_migrations()) == 1

    application.create_migration_file_template(migration2.name, migration2.version)
    application.applied.append_migration(migration2)

    assert len(query_service.get_applied_migrations()) == 2
    assert [m.version for m in query_service.get_applied_migrations(sort_by=pymongo.ASCENDING)] == [1, 2]
    assert [m.version for m in query_service.get_applied_migrations(sort_by=pymongo.DESCENDING)] == [2, 1]


def test_get_applied_migrations_count(
    application: MigrationUI,
    query_service: MigrationQueryService,
    migration: Migration,
    tmp_path: pathlib.Path,
) -> None:
    # Reloading temp migrations dir
    application.config.migration_scripts_dir = str(tmp_path)

    assert query_service.get_applied_migrations_count() == 0

    application.create_migration_file_template(migration.name, migration.version)
    application.applied.append_migration(migration)

    assert query_service.get_applied_migrations_count() == 1


def test_get_first_applied_migration(
    application: MigrationUI,
    query_service: MigrationQueryService,
    migration: Migration,
    migration2: Migration,
    tmp_path: pathlib.Path,
) -> None:
    # Reloading temp migrations dir
    application.config.migration_scripts_dir = str(tmp_path)

    assert query_service.get_first_applied_migration() is None

    application.create_migration_file_template(migration.name, migration.version)
    application.applied.append_migration(migration)

    assert query_service.get_first_applied_migration().version == 1

    application.create_migration_file_template(migration2.name, migration2.version)
    application.applied.append_migration(migration2)

    assert query_service.get_first_applied_migration().version == 1


def test_get_latest_applied_migration(
    application: MigrationUI,
    query_service: MigrationQueryService,
    migration: Migration,
    migration2: Migration,
    tmp_path: pathlib.Path,
) -> None:
    # Reloading temp migrations dir
    application.config.migration_scripts_dir = str(tmp_path)

    assert query_service.get_latest_applied_migration() is None

    application.create_migration_file_template(migration.name, migration.version)
    application.applied.append_migration(migration)

    assert query_service.get_latest_applied_migration().version == 1

    application.create_migration_file_template(migration2.name, migration2.version)
    application.applied.append_migration(migration2)

    assert query_service.get_latest_applied_migration().version == 2


def test_get_applied_waiting_migration_LIFO(
    application: MigrationUI,
    query_service: MigrationQueryService,
    migration: Migration,
    migration2: Migration,
    tmp_path: pathlib.Path,
) -> None:
    # Reloading temp migrations dir
    application.config.migration_scripts_dir = str(tmp_path)

    assert query_service.get_applied_waiting_migration() is None

    application.create_migration_file_template(migration.name, migration.version)
    application.applied.append_migration(migration)

    assert query_service.get_applied_waiting_migration().version == 1

    application.create_migration_file_template(migration2.name, migration2.version)
    application.applied.append_migration(migration2)

    assert query_service.get_applied_waiting_migration().version == 2


def test_get_migrations_count(
    application: MigrationUI,
    query_service: MigrationQueryService,
    migration: Migration,
    migration2: Migration,
    tmp_path: pathlib.Path,
) -> None:
    # Reloading temp migrations dir
    application.config.migration_scripts_dir = str(tmp_path)

    assert query_service.get_migrations_count() == 0

    # Applied
    application.create_migration_file_template(migration.name, migration.version)
    application.applied.append_migration(migration)

    assert query_service.get_migrations_count() == 1

    # Pending
    application.create_migration_file_template(migration2.name, migration2.version)
    application.pending.append_migration(migration2)

    assert query_service.get_migrations_count() == 2
