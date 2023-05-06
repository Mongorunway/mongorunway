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

__all__: typing.Sequence[str] = ("BaseAuditlogJournal",)

import datetime
import typing

import pymongo.collection

from mongorunway.tracking.application.ports.auditlog_journal import AuditlogJournal
from mongorunway.tracking.domain.auditlog_entry import entry_registry

if typing.TYPE_CHECKING:
    from mongorunway.tracking.domain.auditlog_entry import EntryTypeRegistry
    from mongorunway.tracking.domain.auditlog_entry import AuditlogEntry


class BaseAuditlogJournal(AuditlogJournal):
    """Base auditlog journal implementation.

    Parameters
    ----------
    auditlog_collection : Collection[Dict[str, Any]]
        Collection to store auditlog entries.
    registry : EntryTypeRegistry, optional
        Registry of entry types, by default the global `entry_registry`.
    """

    __slots__: typing.Sequence[str] = ("_collection", "_registry")

    def __init__(
        self,
        auditlog_collection: pymongo.collection.Collection[typing.Dict[str, typing.Any]],
        *,
        registry: EntryTypeRegistry = entry_registry,
    ) -> None:
        self._collection = auditlog_collection
        self._registry = registry

    def append_entry(self, entry: AuditlogEntry, /) -> None:
        """Appends a new audit log entry to the journal.

        Parameters
        ----------
        entry: AuditlogEntry
            The audit log entry to be appended.
        """
        self._collection.insert_one(entry.schema())

    def append_entries(self, entries: typing.Sequence[AuditlogEntry], /) -> None:
        """Appends a sequence of audit log entries to the journal.

        Parameters
        ----------
        entries: Sequence[AuditlogEntry]
            The sequence of audit log entries to be appended.
        """
        self._collection.insert_many([e.schema() for e in entries])

    def load_entries(self, limit: typing.Optional[int] = None, /) -> typing.Sequence[AuditlogEntry]:
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
        schemas = self._collection.find({})
        if limit is not None:
            schemas = schemas.limit(limit)

        return [self._registry.get_entry_type(schema["name"]).from_schema(schema) for schema in schemas]

    def history(
        self,
        start: typing.Optional[datetime.datetime] = None,
        end: typing.Optional[datetime.datetime] = None,
        *,
        limit: typing.Optional[int] = None,
    ) -> typing.Iterator[AuditlogEntry]:
        """Returns an iterator over audit log entries within the specified time range.

        Parameters
        ----------
        start: Optional[datetime.datetime]
            The start time for the audit log entries. If not specified, all entries
            before the end time are returned.
        end: Optional[datetime.datetime]
            The end time for the audit log entries. If not specified, all entries
            after the start time are returned.
        limit : Optional[int], default None
            The maximum number of audit log entries to return. If not specified, all
            entries within the specified time range are returned.

        Yields
        ------
        AuditlogEntry
            An audit log entry within the specified time range.
        """
        date_query = {}
        if start is not None:
            date_query["$gte"] = start

        if end is not None:
            date_query["$lte"] = end

        query = {"date": date_query}
        if not date_query:
            # Finding all migrations
            query.clear()

        schemas = self._collection.find(query)
        if limit is not None:
            schemas = schemas.limit(limit)

        for schema in schemas:
            entry_type = self._registry.get_entry_type(schema["name"])
            yield entry_type.from_schema(schema)
