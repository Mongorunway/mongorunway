from __future__ import annotations

import json
import pathlib

from custom_repository_case.json_repository import JSONRepositoryImpl
import pytest

from mongorunway.application.ports import repository as repository_port
from mongorunway.domain import migration as domain_migration


@pytest.fixture(scope="function")
def test_migration() -> domain_migration.Migration:
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
def test_migration2() -> domain_migration.Migration:
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


class TestJSONRepositoryImpl:
    @pytest.fixture
    def repository(self, tmp_path: pathlib.Path) -> repository_port.MigrationModelRepository:
        file_path = tmp_path / "test_migrations.json"
        file_path.touch()
        with open(file_path, "w") as f:
            json.dump({}, f)

        return JSONRepositoryImpl(str(file_path))

    def test_assert_implements(self) -> None:
        assert issubclass(JSONRepositoryImpl, repository_port.MigrationModelRepository)

    def test_len(
        self,
        repository: repository_port.MigrationModelRepository,
        test_migration: domain_migration.Migration,
    ) -> None:
        assert len(repository) == 0
        repository.append_migration(test_migration)
        assert len(repository) == 1

    def test_contains(
        self,
        repository: repository_port.MigrationModelRepository,
        test_migration: domain_migration.Migration,
    ) -> None:
        assert test_migration not in repository
        repository.append_migration(test_migration)
        assert test_migration in repository

    def test_has_migration(
        self,
        repository: repository_port.MigrationModelRepository,
        test_migration: domain_migration.Migration,
    ) -> None:
        assert not repository.has_migration(1)
        assert not repository.has_migration(test_migration)

        repository.append_migration(test_migration)
        assert repository.has_migration(test_migration)

    def test_has_migrations(
        self,
        repository: repository_port.MigrationModelRepository,
        test_migration: domain_migration.Migration,
    ) -> None:
        assert not repository.has_migrations()
        repository.append_migration(test_migration)
        assert repository.has_migrations()

    def test_has_migration_with_version(
        self,
        repository: repository_port.MigrationModelRepository,
        test_migration: domain_migration.Migration,
    ) -> None:
        assert not repository.has_migration_with_version(test_migration.version)
        repository.append_migration(test_migration)
        assert repository.has_migration_with_version(test_migration.version)

    def test_acquire_migration_model_by_version(
        self,
        repository: repository_port.MigrationModelRepository,
        test_migration: domain_migration.Migration,
    ) -> None:
        assert repository.acquire_migration_model_by_version(test_migration.version) is None

        repository.append_migration(test_migration)
        model = repository.acquire_migration_model_by_version(test_migration.version)

        assert model.version == test_migration.version
        assert model.name == test_migration.name
        assert model.is_applied == test_migration.is_applied
        assert model.checksum == test_migration.checksum
        assert model.description == test_migration.description

    def test_acquire_migration_model_by_flag(
        self,
        repository: repository_port.MigrationModelRepository,
        test_migration: domain_migration.Migration,
    ) -> None:
        assert repository.acquire_migration_model_by_flag(is_applied=False) is None
        assert not test_migration.is_applied

        repository.append_migration(test_migration)
        model = repository.acquire_migration_model_by_flag(is_applied=False)

        assert model.version == test_migration.version
        assert model.name == test_migration.name
        assert model.is_applied == test_migration.is_applied
        assert model.checksum == test_migration.checksum
        assert model.description == test_migration.description

    def test_acquire_migration_models_by_flag(
        self,
        repository: repository_port.MigrationModelRepository,
        test_migration: domain_migration.Migration,
        test_migration2: domain_migration.Migration,
    ) -> None:
        assert repository.acquire_migration_model_by_flag(is_applied=False) is None
        assert not test_migration.is_applied
        assert not test_migration2.is_applied

        repository.append_migration(test_migration)
        repository.append_migration(test_migration2)
        models = list(repository.acquire_migration_models_by_flag(is_applied=False))
        assert len(models) == 2

    def test_acquire_all_migration_models(
        self,
        repository: repository_port.MigrationModelRepository,
        test_migration: domain_migration.Migration,
        test_migration2: domain_migration.Migration,
    ) -> None:
        assert repository.acquire_migration_model_by_version(test_migration.version) is None
        assert not test_migration.is_applied
        assert not test_migration2.is_applied

        repository.append_migration(test_migration)
        repository.append_migration(test_migration2)
        models = repository.acquire_all_migration_models()
        assert len(list(models)) == 2

    def test_append_migration(
        self,
        repository: repository_port.MigrationModelRepository,
        test_migration: domain_migration.Migration,
    ) -> None:
        assert test_migration not in repository
        repository.append_migration(test_migration)
        assert test_migration in repository

    def test_remove_migration(
        self,
        repository: repository_port.MigrationModelRepository,
        test_migration: domain_migration.Migration,
        test_migration2: domain_migration.Migration,
    ) -> None:
        assert test_migration not in repository
        repository.append_migration(test_migration)
        repository.append_migration(test_migration2)
        assert test_migration in repository

        repository.remove_migration(test_migration.version)
        assert test_migration not in repository
        assert test_migration2 in repository

    def test_set_applied_flag(
        self,
        repository: repository_port.MigrationModelRepository,
        test_migration: domain_migration.Migration,
    ) -> None:
        repository.append_migration(test_migration)
        assert not repository.acquire_migration_model_by_version(test_migration.version).is_applied

        repository.set_applied_flag(test_migration, is_applied=True)
        assert repository.acquire_migration_model_by_version(test_migration.version).is_applied
