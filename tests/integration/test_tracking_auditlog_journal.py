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
import typing
from unittest import mock

import pytest
import pymongo.database

from mongorunway.tracking.persistence.auditlog_journals import BaseAuditlogJournal
from mongorunway.tracking.domain.auditlog_entry import AuditlogEntry, EntryTypeRegistry


class TestBaseAuditlogJournal:
    @pytest.fixture(scope="function")
    def base_auditlog_journal(
        self, mongodb: pymongo.database.Database[typing.Dict[str, typing.Any]],
    ) -> BaseAuditlogJournal:
        return BaseAuditlogJournal(mongodb.auditlog_collection, registry=EntryTypeRegistry())

    def test_append_entry(self, base_auditlog_journal: BaseAuditlogJournal) -> None:
        entry = AuditlogEntry.new()
        base_auditlog_journal._registry.register(type(entry))

        assert len(base_auditlog_journal.load_entries()) == 0

        base_auditlog_journal.append_entry(entry)

        assert len(base_auditlog_journal.load_entries()) == 1

    def test_append_entries(self, base_auditlog_journal: BaseAuditlogJournal) -> None:
        entry = AuditlogEntry.new()
        base_auditlog_journal._registry.register(type(entry))

        assert len(base_auditlog_journal.load_entries()) == 0

        base_auditlog_journal.append_entries([entry, entry])

        assert len(base_auditlog_journal.load_entries()) == 2

    def test_load_entries(self, base_auditlog_journal: BaseAuditlogJournal) -> None:
        entry = AuditlogEntry.new()
        base_auditlog_journal._registry.register(type(entry))

        assert len(base_auditlog_journal.load_entries()) == 0

        base_auditlog_journal.append_entries([entry, entry, entry])

        assert len(base_auditlog_journal.load_entries()) == 3
        assert len(base_auditlog_journal.load_entries(1)) == 1

    def test_history(self, base_auditlog_journal: BaseAuditlogJournal) -> None:
        entry = AuditlogEntry.new()
        base_auditlog_journal._registry.register(type(entry))
        assert len(list(base_auditlog_journal.history())) == 0

        base_auditlog_journal.append_entries([entry, entry, entry])
        assert len(list(base_auditlog_journal.history())) == 3
        assert len(list(base_auditlog_journal.history(limit=1))) == 1

    def test_history_with_start_and_end(self) -> None:
        entry = AuditlogEntry.new()
        registry = EntryTypeRegistry()
        registry.register(type(entry))

        start = datetime.datetime(2022, 1, 1, 0, 0, 0)
        end = datetime.datetime(2022, 1, 31, 0, 0, 0)

        mock_collection = mock.MagicMock()
        mock_schema1 = {"name": "AuditlogEntry", "date": datetime.datetime(2022, 1, 10, 0, 0, 0)}
        mock_schema2 = {"name": "AuditlogEntry", "date": datetime.datetime(2022, 1, 20, 0, 0, 0)}
        mock_schemas = [mock_schema1, mock_schema2]
        mock_collection.find.return_value = mock_schemas

        my_class = BaseAuditlogJournal(mock_collection, registry=registry)

        result = list(my_class.history(start=start, end=end))

        assert len(result) == 2
        assert isinstance(result[0], AuditlogEntry)
        assert isinstance(result[1], AuditlogEntry)
        assert result[0].name == "AuditlogEntry"
        assert result[1].name == "AuditlogEntry"

        mock_collection.find.assert_called_once_with(
            {"date": {"$gte": start, "$lte": end}}
        )
