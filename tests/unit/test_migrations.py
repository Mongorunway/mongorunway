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

from mongorunway.kernel.domain.migration import Migration, MigrationReadModel
from mongorunway.kernel.infrastructure.migrations import BaseMigration


def test_migration() -> None:
    migration = BaseMigration(
        version=1,
        name="abc",
        checksum="abc",
        description="abc",
        upgrade_commands=[],
        downgrade_commands=[],
    )

    assert migration.version == 1
    assert migration.name == "abc"
    assert migration.checksum == "abc"
    assert migration.description == "abc"
    assert not migration.upgrade_commands
    assert not migration.downgrade_commands

    assert migration.to_mongo_dict() == {
        "_id": 1,
        "version": 1,
        "name": "abc",
        "checksum": "abc",
        "description": "abc",
    }


def test_migration_read_model(migration: Migration) -> None:
    migration_read_model = MigrationReadModel.from_migration(migration)

    assert migration_read_model.name == migration.name
    assert migration_read_model.version == migration.version
    assert migration_read_model.checksum == migration.checksum
    assert migration_read_model.description == migration.description

    assert not hasattr(migration_read_model, "upgrade_commands")
    assert not hasattr(migration_read_model, "downgrade_commands")
