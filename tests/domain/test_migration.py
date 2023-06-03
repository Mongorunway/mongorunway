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

from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_business_rule as domain_rule

if typing.TYPE_CHECKING:
    from mongorunway import mongo


class FakeRule(domain_rule.AbstractMigrationBusinessRule):
    def render_broken_rule(self) -> str:
        pass

    def check_is_broken(self, client: mongo.Client) -> bool:
        pass


@pytest.fixture
def test_migration() -> domain_migration.Migration:
    upgrade_process = domain_migration.MigrationProcess([], 1, "abc")
    downgrade_process = domain_migration.MigrationProcess([], 1, "abc")

    return domain_migration.Migration(
        name="test_migration",
        version=1,
        checksum="abc123",
        is_applied=True,
        description="Test migration",
        upgrade_process=upgrade_process,
        downgrade_process=downgrade_process,
    )


@pytest.fixture
def test_migration_dict() -> typing.Dict[str, typing.Any]:
    return {
        "name": "test",
        "version": 1,
        "checksum": "123",
        "description": "Test description",
        "is_applied": False,
    }


class TestMigration:
    def test_migration_properties(self, test_migration: domain_migration.Migration) -> None:
        assert test_migration.name == "test_migration"
        assert test_migration.version == 1
        assert test_migration.checksum == "abc123"
        assert test_migration.is_applied
        assert test_migration.description == "Test migration"
        assert test_migration.upgrade_process.commands == []
        assert test_migration.upgrade_process.migration_version == 1
        assert test_migration.downgrade_process.commands == []
        assert test_migration.downgrade_process.migration_version == 1

    def test_set_is_applied(self, test_migration: domain_migration.Migration) -> None:
        assert test_migration.is_applied
        test_migration.set_is_applied(False)
        assert not test_migration.is_applied

    def test_to_dict(self, test_migration: domain_migration.Migration) -> None:
        expected_dict = {
            "name": "test_migration",
            "version": 1,
            "checksum": "abc123",
            "is_applied": True,
            "description": "Test migration",
        }
        assert test_migration.to_dict() == expected_dict

    def test_to_dict_with_unique_id(self, test_migration: domain_migration.Migration) -> None:
        expected_dict = {
            "_id": 1,
            "name": "test_migration",
            "version": 1,
            "checksum": "abc123",
            "is_applied": True,
            "description": "Test migration",
        }
        assert test_migration.to_dict(unique=True) == expected_dict


class TestMigrationReadModel:
    def test_from_dict(self, test_migration_dict: typing.Dict[str, typing.Any]) -> None:
        read_model = domain_migration.MigrationReadModel.from_dict(test_migration_dict)

        assert read_model.name == test_migration_dict["name"]
        assert read_model.version == test_migration_dict["version"]
        assert read_model.checksum == test_migration_dict["checksum"]
        assert read_model.description == test_migration_dict["description"]
        assert read_model.is_applied == test_migration_dict["is_applied"]

    def test_from_migration(self, test_migration: domain_migration.Migration) -> None:
        read_model = domain_migration.MigrationReadModel.from_migration(test_migration)

        assert read_model.name == test_migration.name
        assert read_model.version == test_migration.version
        assert read_model.checksum == test_migration.checksum
        assert read_model.description == test_migration.description
        assert read_model.is_applied == test_migration.is_applied


class TestMigrationProcess:
    def test_name(self) -> None:
        migration = domain_migration.MigrationProcess([], 1, "my_migration")

        assert migration.name == "my_migration"

    def test_commands(self) -> None:
        migration = domain_migration.MigrationProcess([], 1, "my_migration")

        assert migration.commands == []

    def test_migration_version(self) -> None:
        migration = domain_migration.MigrationProcess([], 1, "my_migration")

        assert migration.migration_version == 1

    def test_has_rules_initially(self) -> None:
        migration = domain_migration.MigrationProcess([], 1, "my_migration")

        assert not migration.has_rules()

    def test_add_rule(self) -> None:
        migration = domain_migration.MigrationProcess([], 1, "my_migration")
        migration.add_rule(FakeRule())

        assert migration.has_rules()
        assert len(migration.rules) == 1
        assert isinstance(migration.rules[0], FakeRule)
