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
"""The module contains an implementation of the migration audit log interface."""
from __future__ import annotations

__all__: typing.Sequence[str] = ("AuditlogJournalImpl",)

import dataclasses
import datetime
import typing

import pymongo

from mongorunway.application.ports import auditlog_journal as auditlog_journal_port
from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_auditlog_entry as domain_auditlog_entry

if typing.TYPE_CHECKING:
    from mongorunway import mongo


class AuditlogJournalImpl(auditlog_journal_port.AuditlogJournal):
    """Base auditlog journal implementation.

    Parameters
    ----------
    auditlog_collection : Collection[Dict[str, Any]]
        Collection to store auditlog entries.
    """

    __slots__: typing.Sequence[str] = ("_collection", "_max_records")

    def __init__(
        self,
        auditlog_collection: mongo.Collection,
        max_records: typing.Optional[int] = None,
    ) -> None:
        self._max_records = max_records
        self._collection = auditlog_collection

    def append_entries(
        self,
        entries: typing.Sequence[domain_auditlog_entry.MigrationAuditlogEntry],
    ) -> None:
        """Appends a sequence of audit log entries to the journal.

        Parameters
        ----------
        entries: Sequence[Migration]
            The sequence of audit log entries to be appended.
        """
        total = self._collection.count_documents(
            {},
            comment="Get the total count of documents to check the limit.",
        )

        if self._max_records is not None:
            remove = max(0, total - self._max_records + len(entries))
            if remove:
                ids = [r["_id"] for r in self._collection.find().limit(remove)]

                self._collection.delete_many(
                    {"_id": {"$in": ids}},
                    comment="Delete extra records based on the FIFO algorithm.",
                )

        self._collection.insert_many(
            [dataclasses.asdict(entry) for entry in entries],
            # Audit log records have an automatically generated
            # identifier that does not need to be sorted.
            ordered=False,
            comment="Add all audit log entries to the collection.",
        )

    def load_entries(
        self, limit: typing.Optional[int] = None
    ) -> typing.Sequence[domain_auditlog_entry.MigrationAuditlogEntry]:
        """Returns a sequence of audit log entries from the journal.

        Parameters
        ----------
        limit: Optional[int]
            The maximum number of entries to return. If not specified, all entries are returned.

        Returns
        -------
        List[AuditlogEntry]
            A sequence of audit log entries from the journal.
        """
        pipeline: typing.List[typing.Any] = [{"$match": {}}]
        if limit is not None:
            pipeline.append({"$limit": limit})

        entries = [
            domain_auditlog_entry.MigrationAuditlogEntry.from_dict(entry)
            for entry in self._collection.aggregate(
                pipeline,
                comment=f"Loading all records with a limit of {'none' if limit is None else limit}.",
            )
        ]

        return entries

    def history(
        self,
        start: typing.Optional[datetime.datetime] = None,
        end: typing.Optional[datetime.datetime] = None,
        limit: typing.Optional[int] = None,
        ascending_date: bool = True,
    ) -> typing.Iterator[domain_auditlog_entry.MigrationAuditlogEntry]:
        pipeline: typing.List[typing.Any] = [
            {"$sort": {"date": pymongo.ASCENDING if ascending_date else pymongo.DESCENDING}}
        ]
        if start is not None:
            pipeline.append({"$match": {"date": {"$gte": start}}})
        if end is not None:
            pipeline.append({"$match": {"date": {"$lte": end}}})
        if limit is not None:
            pipeline.append({"$limit": limit})

        schemas = self._collection.aggregate(pipeline)

        for schema in schemas:
            schema["migration"] = domain_migration.MigrationReadModel.from_dict(
                schema["migration"],
            )
            yield domain_auditlog_entry.MigrationAuditlogEntry.from_dict(schema)
