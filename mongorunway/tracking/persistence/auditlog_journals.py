from __future__ import annotations

__all__: typing.Sequence[str] = ("BaseAuditlogJournal",)

import datetime
import typing

import pymongo.collection

from mongorunway.tracking.application.ports.auditlog_journal import AuditlogJournal
from mongorunway.tracking.domain.auditlog_entry import entry_registry

if typing.TYPE_CHECKING:
    from mongorunway.tracking.domain.auditlog_entry import AuditlogEntry


class BaseAuditlogJournal(AuditlogJournal):
    __slots__: typing.Sequence[str] = ("_collection",)

    def __init__(
        self, auditlog_collection: pymongo.collection.Collection[typing.Dict[str, typing.Any]], /
    ) -> None:
        self._collection = auditlog_collection

    def append_entry(self, entry: AuditlogEntry, /) -> None:
        self._collection.insert_one(entry.schema())

    def append_entries(self, entries: typing.Sequence[AuditlogEntry], /) -> None:
        self._collection.insert_many([e.schema() for e in entries])

    def load_entries(self, limit: typing.Optional[int] = None, /) -> typing.Sequence[AuditlogEntry]:
        schemas = self._collection.find({})
        if limit is not None:
            schemas = schemas.limit(limit)

        return [entry_registry.get_entry_type(schema["name"]).from_schema(schema) for schema in schemas]

    def history(
        self,
        start: typing.Optional[datetime.datetime] = None,
        end: typing.Optional[datetime.datetime] = None,
        *,
        limit: typing.Optional[int] = None,
    ) -> typing.Iterator[AuditlogEntry]:
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
            entry_type = entry_registry.get_entry_type(schema["name"])
            yield entry_type.from_schema(schema)
