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

from mongorunway.domain.migration import Migration
from mongorunway.application.ui import MigrationUiImpl
from mongorunway.application.config import (
    Config, ApplicationConfig, FileSystemConfig, MongoDBConfig
)
from mongorunway.infrastructure.persistence.repositories import MigrationRepositoryImpl
from mongorunway.infrastructure.filename_strategies import MissingFilenameStrategy

if typing.TYPE_CHECKING:
    from mongorunway import types
    from mongorunway.application.ui import MigrationUi

APP_NAME: typing.Final[str] = "test"


@pytest.fixture(scope="function")
def tmp_migration_path(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "test_migrations"


@pytest.fixture(scope="function")
def config(mongodb: types.MongoDatabase, tmp_migration_path: pathlib.Path) -> Config:
    cfg = Config(
        application=ApplicationConfig(
            disable_loggers=True,
            name="test",
        ),
        filesystem=FileSystemConfig(
            config_dir="abc",
            filename_strategy=MissingFilenameStrategy(),
            scripts_dir=str(tmp_migration_path),
        ),
        mongodb=MongoDBConfig(
            auditlog_collection=None,
            client=mongodb.client,
            database=mongodb,
            migrations_collection=mongodb.test_migrations,
        ),
    )

    return cfg


@pytest.fixture(scope="function")
def application(config: Config) -> MigrationUi:
    return MigrationUiImpl(
        config,
        auditlog_journal=None,
        repository=MigrationRepositoryImpl(config.mongodb.migrations_collection),
        startup_hooks=config.application.startup_hooks,
    )


@pytest.fixture(scope="function")
def migration() -> Migration:
    return Migration(
        checksum="123",
        description="123",
        downgrade_commands=[],
        upgrade_commands=[],
        version=1,
        name="123",
        is_applied=False,
    )


@pytest.fixture(scope="function")
def migration2() -> Migration:
    return Migration(
        checksum="321",
        description="321",
        downgrade_commands=[],
        upgrade_commands=[],
        version=2,
        name="321",
        is_applied=False,
    )
