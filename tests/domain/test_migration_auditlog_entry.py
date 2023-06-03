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

import zoneinfo

import bson
import pytest

from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_auditlog_entry as domain_entry


@pytest.fixture
def test_entry(migration: domain_migration.Migration) -> domain_entry.MigrationAuditlogEntry:
    return domain_entry.MigrationAuditlogEntry(
        session_id=bson.Binary("abc".encode()),
        transaction_name="transaction",
        migration_read_model=domain_migration.MigrationReadModel.from_migration(migration),
        date_fmt="abc",
    )


def test_from_dict(
    test_entry: domain_entry.MigrationAuditlogEntry,
    migration: domain_migration.Migration,
) -> None:
    test_entry_dict = dict(
        session_id=bson.Binary("abc".encode()),
        transaction_name="transaction",
        migration_read_model=domain_migration.MigrationReadModel.from_migration(migration),
        date_fmt="abc",
    )
    entry = domain_entry.MigrationAuditlogEntry.from_dict(test_entry_dict)
    assert entry.session_id == test_entry_dict["session_id"]
    assert entry.transaction_name == test_entry_dict["transaction_name"]


def test_is_failed_initially(migration: domain_migration.Migration) -> None:
    entry = domain_entry.MigrationAuditlogEntry(
        session_id=bson.Binary("abc".encode()),
        transaction_name="transaction",
        migration_read_model=domain_migration.MigrationReadModel.from_migration(migration),
        date_fmt="abc",
    )
    assert not entry.is_failed()


def test_with_error(test_entry: domain_entry.MigrationAuditlogEntry) -> None:
    exc = ValueError("Some error")
    test_entry = test_entry.with_error(exc)

    assert test_entry.is_failed()
    assert test_entry.exc_name == "ValueError"
    assert test_entry.exc_message == "Some error"


def test_with_timezone(test_entry: domain_entry.MigrationAuditlogEntry) -> None:
    test_entry = test_entry.with_timezone("Europe/Paris")

    assert test_entry.date.tzinfo == zoneinfo.ZoneInfo("Europe/Paris")


def test_format_date(test_entry: domain_entry.MigrationAuditlogEntry) -> None:
    test_entry.date_fmt = "%Y/%m/%d"
    assert test_entry.format_date() == test_entry.date.strftime(test_entry.date_fmt)
