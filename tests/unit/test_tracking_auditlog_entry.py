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

import datetime

import pytest

from mongorunway.kernel.domain.migration import MigrationReadModel
from mongorunway.tracking.domain.auditlog_entry import EntryTypeRegistry, AuditlogEntry
from mongorunway.tracking.domain.auditlog_entry import (
    MigrationUpgraded,
    MigrationDowngraded,
    PendingMigrationAdded,
    PendingMigrationRemoved,
    BulkMigrationUpgraded,
    BulkMigrationDowngraded,
)


@pytest.fixture(scope="function")
def migration_read_model() -> MigrationReadModel:
    return MigrationReadModel(version=1, name="migration_1", checksum="abc", description="abc")


class FakeAuditlogEntry(AuditlogEntry):
    pass


def test_entry_registry() -> None:
    registry = EntryTypeRegistry()

    assert registry.get_entry_type("FakeAuditlogEntry") is None

    registry.register(FakeAuditlogEntry)

    assert registry.get_entry_type("FakeAuditlogEntry") is FakeAuditlogEntry


class TestAuditlogEntry:
    def test_alternative_initializer(self) -> None:
        entry = AuditlogEntry.new()

        assert entry.name == "AuditlogEntry"
        assert isinstance(entry.date, datetime.datetime)

    def test_from_schema(self) -> None:
        entry = AuditlogEntry.from_schema({"name": "abc"})
        assert entry.name == "abc"

        from_mongo_schema = AuditlogEntry.from_schema({"_id": 1, "name": "abc"})
        assert from_mongo_schema.name == "abc"

    def test_schema(self) -> None:
        entry = AuditlogEntry.new()
        schema = entry.schema()

        assert schema.get("name") == "AuditlogEntry"
        assert isinstance(schema.get("date"), datetime.datetime)

    def test_with_timezone(self) -> None:
        entry = AuditlogEntry.new()
        assert entry.date == entry.with_time_zone("UTC").date

        # Requires `tzdata` module
        assert entry.date != entry.with_time_zone("Africa/Abidjan").date


class TestMigrationUpgraded:
    @pytest.fixture
    def migration_upgraded(self, migration_read_model: MigrationReadModel) -> MigrationUpgraded:
        return MigrationUpgraded(
            name="migration_upgraded",
            upgraded_count=1,
            migration_read_model=migration_read_model,
        )

    def test_migration_upgraded(self, migration_upgraded: MigrationUpgraded) -> None:
        assert migration_upgraded.name == "migration_upgraded"
        assert migration_upgraded.upgraded_count == 1
        assert migration_upgraded.migration_read_model.version == 1
        assert migration_upgraded.migration_read_model.name == "migration_1"
        assert isinstance(migration_upgraded.date, datetime.datetime)

    def test_migration_upgraded_schema(self, migration_upgraded: MigrationUpgraded) -> None:
        schema = migration_upgraded.schema()
        assert schema["name"] == "migration_upgraded"
        assert schema["upgraded_count"] == 1
        assert schema["migration_read_model"]["version"] == 1
        assert schema["migration_read_model"]["name"] == "migration_1"

    def test_migration_upgraded_from_schema(self, migration_upgraded: MigrationUpgraded) -> None:
        schema = migration_upgraded.schema()
        new_migration_upgraded = MigrationUpgraded.from_schema(schema)
        assert new_migration_upgraded.name == migration_upgraded.name
        assert new_migration_upgraded.upgraded_count == migration_upgraded.upgraded_count
        assert new_migration_upgraded.migration_read_model.version == migration_upgraded.migration_read_model.version
        assert new_migration_upgraded.migration_read_model.name == migration_upgraded.migration_read_model.name


class TestMigrationDowngraded:
    @pytest.fixture
    def migration_downgraded(self, migration_read_model: MigrationReadModel) -> MigrationDowngraded:
        return MigrationDowngraded(
            name="migration_downgraded",
            downgraded_count=1,
            migration_read_model=migration_read_model,
        )

    def test_migration_downgraded(self, migration_downgraded: MigrationDowngraded) -> None:
        assert migration_downgraded.name == "migration_downgraded"
        assert migration_downgraded.downgraded_count == 1
        assert migration_downgraded.migration_read_model.version == 1
        assert migration_downgraded.migration_read_model.name == "migration_1"
        assert isinstance(migration_downgraded.date, datetime.datetime)

    def test_migration_downgraded_schema(self, migration_downgraded: MigrationDowngraded) -> None:
        schema = migration_downgraded.schema()
        assert schema["name"] == "migration_downgraded"
        assert schema["downgraded_count"] == 1
        assert schema["migration_read_model"]["version"] == 1
        assert schema["migration_read_model"]["name"] == "migration_1"

    def test_migration_downgraded_from_schema(self, migration_downgraded: MigrationDowngraded) -> None:
        schema = migration_downgraded.schema()
        new_migration_upgraded = MigrationDowngraded.from_schema(schema)
        assert new_migration_upgraded.name == migration_downgraded.name
        assert new_migration_upgraded.downgraded_count == migration_downgraded.downgraded_count
        assert new_migration_upgraded.migration_read_model.version == migration_downgraded.migration_read_model.version
        assert new_migration_upgraded.migration_read_model.name == migration_downgraded.migration_read_model.name


class TestPendingMigrationAdded:
    @pytest.fixture
    def pending_migration_added(self, migration_read_model: MigrationReadModel) -> PendingMigrationAdded:
        return PendingMigrationAdded(
            name="pending_migration_added",
            migration_read_model=migration_read_model,
        )

    def test_pending_migration_added(self, pending_migration_added: PendingMigrationAdded) -> None:
        assert pending_migration_added.name == "pending_migration_added"
        assert pending_migration_added.migration_read_model.version == 1
        assert pending_migration_added.migration_read_model.name == "migration_1"
        assert isinstance(pending_migration_added.date, datetime.datetime)

    def test_pending_migration_added_schema(self, pending_migration_added: PendingMigrationAdded) -> None:
        schema = pending_migration_added.schema()
        assert schema["name"] == "pending_migration_added"
        assert schema["migration_read_model"]["version"] == 1
        assert schema["migration_read_model"]["name"] == "migration_1"

    def test_pending_migration_added_from_schema(self, pending_migration_added: PendingMigrationAdded) -> None:
        schema = pending_migration_added.schema()
        new_migration_upgraded = PendingMigrationAdded.from_schema(schema)
        assert new_migration_upgraded.name == pending_migration_added.name
        assert new_migration_upgraded.migration_read_model.version == pending_migration_added.migration_read_model.version
        assert new_migration_upgraded.migration_read_model.name == pending_migration_added.migration_read_model.name


class TestPendingMigrationRemoved:
    @pytest.fixture
    def pending_migration_removed(self, migration_read_model: MigrationReadModel) -> PendingMigrationRemoved:
        return PendingMigrationRemoved(
            name="pending_migration_removed",
            migration_read_model=migration_read_model,
        )

    def test_pending_migration_removed(self, pending_migration_removed: PendingMigrationRemoved) -> None:
        assert pending_migration_removed.name == "pending_migration_removed"
        assert pending_migration_removed.migration_read_model.version == 1
        assert pending_migration_removed.migration_read_model.name == "migration_1"
        assert isinstance(pending_migration_removed.date, datetime.datetime)

    def test_pending_migration_removed_schema(self, pending_migration_removed: PendingMigrationRemoved) -> None:
        schema = pending_migration_removed.schema()
        assert schema["name"] == "pending_migration_removed"
        assert schema["migration_read_model"]["version"] == 1
        assert schema["migration_read_model"]["name"] == "migration_1"

    def test_pending_migration_removed_from_schema(self, pending_migration_removed: PendingMigrationRemoved) -> None:
        schema = pending_migration_removed.schema()
        new_migration_upgraded = PendingMigrationRemoved.from_schema(schema)
        assert new_migration_upgraded.name == pending_migration_removed.name
        assert new_migration_upgraded.migration_read_model.version == pending_migration_removed.migration_read_model.version
        assert new_migration_upgraded.migration_read_model.name == pending_migration_removed.migration_read_model.name


class TestBulkMigrationUpgraded:
    @pytest.fixture
    def bulk_migration_upgraded(self, migration_read_model: MigrationReadModel) -> BulkMigrationUpgraded:
        return BulkMigrationUpgraded(
            name="bulk_migration_upgraded",
            upgraded_count=1,
            upgraded_migrations=[migration_read_model],
        )

    def test_migration_upgraded(self, bulk_migration_upgraded: BulkMigrationUpgraded) -> None:
        assert bulk_migration_upgraded.name == "bulk_migration_upgraded"
        assert bulk_migration_upgraded.upgraded_count == 1
        assert len(bulk_migration_upgraded.upgraded_migrations) == 1
        assert isinstance(bulk_migration_upgraded.date, datetime.datetime)

    def test_migration_upgraded_schema(self, bulk_migration_upgraded: BulkMigrationUpgraded) -> None:
        schema = bulk_migration_upgraded.schema()
        assert schema["name"] == "bulk_migration_upgraded"
        assert schema["upgraded_count"] == 1
        assert len(schema["upgraded_migrations"]) == 1

    def test_migration_upgraded_from_schema(self, bulk_migration_upgraded: BulkMigrationUpgraded) -> None:
        schema = bulk_migration_upgraded.schema()
        new_migration_upgraded = BulkMigrationUpgraded.from_schema(schema)
        assert new_migration_upgraded.name == bulk_migration_upgraded.name
        assert new_migration_upgraded.upgraded_count == bulk_migration_upgraded.upgraded_count
        assert new_migration_upgraded.upgraded_migrations[0].version == bulk_migration_upgraded.upgraded_migrations[0].version


class TestBulkMigrationDowngraded:
    @pytest.fixture
    def bulk_migration_downgraded(self, migration_read_model: MigrationReadModel) -> BulkMigrationDowngraded:
        return BulkMigrationDowngraded(
            name="bulk_migration_downgraded",
            downgraded_count=1,
            downgraded_migrations=[migration_read_model],
        )

    def test_migration_upgraded(self, bulk_migration_downgraded: BulkMigrationDowngraded) -> None:
        assert bulk_migration_downgraded.name == "bulk_migration_downgraded"
        assert bulk_migration_downgraded.downgraded_count == 1
        assert len(bulk_migration_downgraded.downgraded_migrations) == 1
        assert isinstance(bulk_migration_downgraded.date, datetime.datetime)

    def test_migration_upgraded_schema(self, bulk_migration_downgraded: BulkMigrationDowngraded) -> None:
        schema = bulk_migration_downgraded.schema()
        assert schema["name"] == "bulk_migration_downgraded"
        assert schema["downgraded_count"] == 1
        assert len(schema["downgraded_migrations"]) == 1

    def test_migration_upgraded_from_schema(self, bulk_migration_downgraded: BulkMigrationDowngraded) -> None:
        schema = bulk_migration_downgraded.schema()
        new_migration_upgraded = BulkMigrationDowngraded.from_schema(schema)
        assert new_migration_upgraded.name == bulk_migration_downgraded.name
        assert new_migration_upgraded.downgraded_count == bulk_migration_downgraded.downgraded_count
        assert new_migration_upgraded.downgraded_migrations[0].version == bulk_migration_downgraded.downgraded_migrations[0].version
