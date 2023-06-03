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

import pytest

from mongorunway.application.ports import repository as repository_port
from mongorunway.infrastructure.persistence.repositories import MongoModelRepositoryImpl

if typing.TYPE_CHECKING:
    from mongorunway import mongo
    from mongorunway.domain import migration as domain_migration


class TestMigrationRepositoryImpl:
    @pytest.fixture
    def repository(self, mongodb: mongo.Database) -> repository_port.MigrationModelRepository:
        return MongoModelRepositoryImpl(mongodb.test_collection)

    def test_assert_implements(self) -> None:
        assert issubclass(MongoModelRepositoryImpl, repository_port.MigrationModelRepository)

    def test_len(
        self,
        repository: repository_port.MigrationModelRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert len(repository) == 0
        repository.append_migration(migration)
        assert len(repository) == 1

    def test_contains(
        self,
        repository: repository_port.MigrationModelRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert migration not in repository
        repository.append_migration(migration)
        assert migration in repository

    def test_has_migration(
        self,
        repository: repository_port.MigrationModelRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert repository.has_migration(1) is NotImplemented
        assert not repository.has_migration(migration)

        repository.append_migration(migration)
        assert repository.has_migration(migration)

    def test_has_migrations(
        self,
        repository: repository_port.MigrationModelRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert not repository.has_migrations()
        repository.append_migration(migration)
        assert repository.has_migrations()

    def test_has_migration_with_version(
        self,
        repository: repository_port.MigrationModelRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert not repository.has_migration_with_version(migration.version)
        repository.append_migration(migration)
        assert repository.has_migration_with_version(migration.version)

    def test_acquire_migration_model_by_version(
        self,
        repository: repository_port.MigrationModelRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert repository.acquire_migration_model_by_version(migration.version) is None

        repository.append_migration(migration)
        model = repository.acquire_migration_model_by_version(migration.version)

        assert model.version == migration.version
        assert model.name == migration.name
        assert model.is_applied == migration.is_applied
        assert model.checksum == migration.checksum
        assert model.description == migration.description

    def test_acquire_migration_model_by_flag(
        self,
        repository: repository_port.MigrationModelRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert repository.acquire_migration_model_by_flag(is_applied=False) is None
        assert not migration.is_applied

        repository.append_migration(migration)
        model = repository.acquire_migration_model_by_flag(is_applied=False)

        assert model.version == migration.version
        assert model.name == migration.name
        assert model.is_applied == migration.is_applied
        assert model.checksum == migration.checksum
        assert model.description == migration.description

    def test_acquire_migration_models_by_flag(
        self,
        repository: repository_port.MigrationModelRepository,
        migration: domain_migration.Migration,
        migration2: domain_migration.Migration,
    ) -> None:
        assert repository.acquire_migration_model_by_flag(is_applied=False) is None
        assert not migration.is_applied
        assert not migration2.is_applied

        repository.append_migration(migration)
        repository.append_migration(migration2)
        models = list(repository.acquire_migration_models_by_flag(is_applied=False))
        assert len(models) == 2

    def test_acquire_all_migration_models(
        self,
        repository: repository_port.MigrationModelRepository,
        migration: domain_migration.Migration,
        migration2: domain_migration.Migration,
    ) -> None:
        assert repository.acquire_migration_model_by_version(migration.version) is None
        assert not migration.is_applied
        assert not migration2.is_applied

        repository.append_migration(migration)
        repository.append_migration(migration2)
        models = repository.acquire_all_migration_models()
        assert len(list(models)) == 2

    def test_append_migration(
        self,
        repository: repository_port.MigrationModelRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert migration not in repository
        repository.append_migration(migration)
        assert migration in repository

    def test_remove_migration(
        self,
        repository: repository_port.MigrationModelRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert migration not in repository
        repository.append_migration(migration)
        assert migration in repository

        repository.remove_migration(migration.version)
        assert migration not in repository

    def test_set_applied_flag(
        self,
        repository: repository_port.MigrationModelRepository,
        migration: domain_migration.Migration,
    ) -> None:
        repository.append_migration(migration)
        assert not repository.acquire_migration_model_by_version(migration.version).is_applied

        repository.set_applied_flag(migration, is_applied=True)
        assert repository.acquire_migration_model_by_version(migration.version).is_applied
