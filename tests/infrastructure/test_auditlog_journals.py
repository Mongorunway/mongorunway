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

import copy
import datetime
import typing

import bson
import pytest

from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_auditlog_entry as domain_entry
from mongorunway.infrastructure.persistence.auditlog_journals import MongoAuditlogJournalImpl

if typing.TYPE_CHECKING:
    from mongorunway import mongo
    from mongorunway.application.ports import auditlog_journal as auditlog_journal_port


@pytest.fixture
def entry(
    mongodb: mongo.Database,
    migration: domain_migration.Migration,
) -> domain_entry.MigrationAuditlogEntry:
    return domain_entry.MigrationAuditlogEntry(
        session_id=bson.Binary("abc".encode()),
        date_fmt="abc",
        migration_read_model=domain_migration.MigrationReadModel.from_migration(migration),
        transaction_name="abc",
        date=datetime.datetime(2023, 5, 3),
    )


@pytest.fixture
def entry2(entry: domain_entry.MigrationAuditlogEntry) -> domain_entry.MigrationAuditlogEntry:
    entry2 = copy.deepcopy(entry)
    entry2.date = datetime.datetime(2023, 5, 1)
    return entry2


@pytest.fixture
def entry3(entry: domain_entry.MigrationAuditlogEntry) -> domain_entry.MigrationAuditlogEntry:
    entry3 = copy.deepcopy(entry)
    entry3.date = datetime.datetime(2023, 5, 2)
    return entry3


class TestAuditlogJournalImpl:
    @pytest.fixture
    def auditlog_journal(self, mongodb: mongo.Database) -> auditlog_journal_port.AuditlogJournal:
        return MongoAuditlogJournalImpl(auditlog_collection=mongodb.test_collection)

    def test_initializes_correctly(
        self,
        auditlog_journal: auditlog_journal_port.AuditlogJournal,
    ) -> None:
        assert auditlog_journal.max_records is None

    def test_set_max_records(
        self,
        auditlog_journal: auditlog_journal_port.AuditlogJournal,
    ) -> None:
        auditlog_journal.set_max_records(123)
        assert auditlog_journal.max_records == 123

    def test_append_entries(
        self,
        auditlog_journal: auditlog_journal_port.AuditlogJournal,
        entry: domain_entry.MigrationAuditlogEntry,
    ) -> None:
        assert len(auditlog_journal.load_entries()) == 0

        auditlog_journal.append_entries([entry, entry, entry])
        assert len(auditlog_journal.load_entries()) == 3

        auditlog_journal.set_max_records(2)
        auditlog_journal.append_entries([entry])
        assert len(auditlog_journal.load_entries()) == 2

    def test_load_entries(
        self,
        auditlog_journal: auditlog_journal_port.AuditlogJournal,
        entry: domain_entry.MigrationAuditlogEntry,
    ) -> None:
        assert len(auditlog_journal.load_entries()) == 0
        auditlog_journal.append_entries([entry, entry, entry])
        assert len(auditlog_journal.load_entries()) == 3
        assert len(auditlog_journal.load_entries(2)) == 2

    def test_history(
        self,
        auditlog_journal: auditlog_journal_port.AuditlogJournal,
        entry: domain_entry.MigrationAuditlogEntry,
    ) -> None:
        auditlog_journal.append_entries([entry, entry, entry])

        assert len(list(auditlog_journal.history())) == 3
        assert len(list(auditlog_journal.history(limit=2))) == 2

    def test_history_date_boundaries(
        self,
        auditlog_journal: auditlog_journal_port.AuditlogJournal,
        entry: domain_entry.MigrationAuditlogEntry,
        entry2: domain_entry.MigrationAuditlogEntry,
        entry3: domain_entry.MigrationAuditlogEntry,
    ) -> None:
        auditlog_journal.append_entries([entry, entry2, entry3])

        entries = list(
            auditlog_journal.history(
                start=datetime.datetime(2023, 5, 2),
                end=datetime.datetime(2023, 5, 3),
            )
        )
        assert len(entries) == 2
        assert entries[0].date == datetime.datetime(2023, 5, 2)
        assert entries[1].date == datetime.datetime(2023, 5, 3)

    def test_history_ascending_date(
        self,
        auditlog_journal: auditlog_journal_port.AuditlogJournal,
        entry: domain_entry.MigrationAuditlogEntry,
        entry2: domain_entry.MigrationAuditlogEntry,
        entry3: domain_entry.MigrationAuditlogEntry,
    ) -> None:
        auditlog_journal.append_entries([entry, entry2, entry3])

        result = list(
            auditlog_journal.history(
                datetime.datetime(2023, 5, 1),
                datetime.datetime(2023, 5, 3),
                2,
                False,
            ),
        )

        assert len(result) == 2
        assert result[0].date == datetime.datetime(2023, 5, 3)
        assert result[1].date == datetime.datetime(2023, 5, 2)

        result = list(
            auditlog_journal.history(
                datetime.datetime(2023, 5, 1),
                datetime.datetime(2023, 5, 3),
                2,
                True,
            ),
        )
        assert result[0].date == datetime.datetime(2023, 5, 1)
        assert result[1].date == datetime.datetime(2023, 5, 2)
