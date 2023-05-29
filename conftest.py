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

from mongorunway.domain import migration as domain_migration
from mongorunway.application import applications
from mongorunway.application import config
from mongorunway.infrastructure.persistence import repositories
from mongorunway.infrastructure import filename_strategies

if typing.TYPE_CHECKING:
    from mongorunway import mongo

APP_NAME: typing.Final[str] = "test"


@pytest.fixture(scope="function")
def tmp_migration_path(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "test_migrations"


@pytest.fixture(scope="function")
def configuration(mongodb: mongo.Database, tmp_migration_path: pathlib.Path) -> config.Config:
    cfg = config.Config(
        application=config.ApplicationConfig(
            use_logging=False,
            use_auditlog=False,
            use_indexing=False,
            use_schema_validation=False,
            app_client=mongodb.client,
            app_database=mongodb,
            app_name=APP_NAME,
            app_repository=repositories.MigrationRepositoryImpl(mongodb.test_migrations),
            app_auditlog_journal=None,
        ),
        filesystem=config.FileSystemConfig(
            config_dir="",
            filename_strategy=filename_strategies.MissingFilenameStrategy(),
            scripts_dir=str(tmp_migration_path),
        ),
        logging_dict={},
    )

    return cfg


@pytest.fixture(scope="function")
def application(configuration: config.Config) -> applications.MigrationApp:
    return applications.MigrationAppImpl(configuration)


@pytest.fixture(scope="function")
def migration() -> domain_migration.Migration:
    return domain_migration.Migration(
        checksum="123",
        description="123",
        downgrade_process=domain_migration.MigrationProcess(
            commands=[],
            migration_version=1,
            name="downgrade",
        ),
        upgrade_process=domain_migration.MigrationProcess(
            commands=[],
            migration_version=1,
            name="upgrade",
        ),
        version=1,
        name="123",
        is_applied=False,
    )


@pytest.fixture(scope="function")
def migration2() -> domain_migration.Migration:
    return domain_migration.Migration(
        checksum="321",
        description="321",
        downgrade_process=domain_migration.MigrationProcess(
            commands=[],
            migration_version=2,
            name="downgrade",
        ),
        upgrade_process=domain_migration.MigrationProcess(
            commands=[],
            migration_version=2,
            name="upgrade",
        ),
        version=2,
        name="321",
        is_applied=False,
    )
