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

import typing

import pymongo.database
import pytest

from mongorunway.kernel.infrastructure.migrations import BaseMigration
from mongorunway.kernel.application.ui import BaseMigrationUI
from mongorunway.kernel.application.config import ApplicationConfig

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration import Migration
    from mongorunway.kernel.application.ui import MigrationUI


@pytest.fixture(scope="function")
def config(mongodb: pymongo.database.Database[typing.Dict[str, typing.Any]]) -> ApplicationConfig:
    cfg = ApplicationConfig.from_dict(
        {
            "root": {
                "scripts_dir": "test_migrations",
            },
            "app_test": {
                "uri": "localhost",
                "port": 27017,
                "database": "test_database",
                "collection_applied": "applied_migrations",
                "collection_pending": "pending_migrations",
            },
            "app_test.auditlog": {
                "collection_auditlog": "auditlog_collection",
            },
        },
        name="test",
    )

    cfg.connection.applied_migration_collection = mongodb.applied_migrations
    cfg.connection.pending_migration_collection = mongodb.pending_migrations

    return cfg


@pytest.fixture(scope="function")
def application(config: ApplicationConfig) -> MigrationUI:
    return BaseMigrationUI(config)


@pytest.fixture(scope="function")
def migration() -> Migration:
    return BaseMigration(
        checksum="123",
        description="123",
        downgrade_commands=[],
        upgrade_commands=[],
        version=1,
        name="123",
    )


@pytest.fixture(scope="function")
def migration2() -> Migration:
    return BaseMigration(
        checksum="321",
        description="321",
        downgrade_commands=[],
        upgrade_commands=[],
        version=2,
        name="321",
    )
