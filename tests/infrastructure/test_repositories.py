from __future__ import annotations

import typing

import pytest

from mongorunway.application.ports import repository as repository_port
from mongorunway.infrastructure.persistence.repositories import MigrationRepositoryImpl

if typing.TYPE_CHECKING:
    from mongorunway import mongo
    from mongorunway.domain import migration as domain_migration


class TestMigrationRepositoryImpl:
    @pytest.fixture
    def repository(self, mongodb: mongo.Database) -> repository_port.MigrationRepository:
        return MigrationRepositoryImpl(mongodb.test_collection)

    def test_assert_implements(self) -> None:
        assert issubclass(MigrationRepositoryImpl, repository_port.MigrationRepository)

    def test_len(
        self,
        repository: repository_port.MigrationRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert len(repository) == 0
        repository.append_migration(migration)
        assert len(repository) == 1

    def test_contains(
        self,
        repository: repository_port.MigrationRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert migration not in repository
        repository.append_migration(migration)
        assert migration in repository

    def test_has_migration(
        self,
        repository: repository_port.MigrationRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert repository.has_migration(1) is NotImplemented
        assert not repository.has_migration(migration)

        repository.append_migration(migration)
        assert repository.has_migration(migration)

    def test_has_migrations(
        self,
        repository: repository_port.MigrationRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert not repository.has_migrations()
        repository.append_migration(migration)
        assert repository.has_migrations()

    def test_has_migration_with_version(
        self,
        repository: repository_port.MigrationRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert not repository.has_migration_with_version(migration.version)
        repository.append_migration(migration)
        assert repository.has_migration_with_version(migration.version)

    def test_acquire_migration_model_by_version(
        self,
        repository: repository_port.MigrationRepository,
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
        repository: repository_port.MigrationRepository,
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
        repository: repository_port.MigrationRepository,
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
        repository: repository_port.MigrationRepository,
        migration: domain_migration.Migration,
        migration2: domain_migration.Migration,
    ) -> None:
        assert repository.acquire_migration_model_by_version(migration.version) is None
        assert not migration.is_applied
        assert not migration2.is_applied

        repository.append_migration(migration)
        repository.append_migration(migration2)
        models = repository.acquire_all_migration_models()
        assert len(models) == 2

    def test_append_migration(
        self,
        repository: repository_port.MigrationRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert migration not in repository
        repository.append_migration(migration)
        assert migration in repository

    def test_remove_migration(
        self,
        repository: repository_port.MigrationRepository,
        migration: domain_migration.Migration,
    ) -> None:
        assert migration not in repository
        repository.append_migration(migration)
        assert migration in repository

        repository.remove_migration(migration.version)
        assert migration not in repository

    def test_set_applied_flag(
        self,
        repository: repository_port.MigrationRepository,
        migration: domain_migration.Migration,
    ) -> None:
        repository.append_migration(migration)
        assert not repository.acquire_migration_model_by_version(migration.version).is_applied

        repository.set_applied_flag(migration, is_applied=True)
        assert repository.acquire_migration_model_by_version(migration.version).is_applied
