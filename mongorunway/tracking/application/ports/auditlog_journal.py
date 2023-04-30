from __future__ import annotations

__all__: typing.Sequence[str] = ("AuditlogJournal",)

import abc
import datetime
import typing

if typing.TYPE_CHECKING:
    from mongorunway.tracking.domain.auditlog_entry import AuditlogEntry


class AuditlogJournal(abc.ABC):
    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def append_entry(self, entry: AuditlogEntry, /) -> None:
        ...

    @abc.abstractmethod
    def append_entries(self, entries: typing.Sequence[AuditlogEntry], /) -> None:
        ...

    @abc.abstractmethod
    def load_entries(self, entries_count: int, /) -> typing.Sequence[AuditlogEntry]:
        ...

    @abc.abstractmethod
    def history(
        self,
        start: typing.Optional[datetime.datetime] = None,
        end: typing.Optional[datetime.datetime] = None,
    ) -> typing.Iterator[AuditlogEntry]:
        ...
