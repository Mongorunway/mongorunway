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

__all__: typing.Sequence[str] = ("AuditlogJournal",)

import abc
import datetime
import typing

if typing.TYPE_CHECKING:
    from mongorunway.domain import migration_auditlog_entry as domain_auditlog_entry


class AuditlogJournal(abc.ABC):
    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def max_records(self) -> typing.Optional[int]:
        ...

    @abc.abstractmethod
    def set_max_records(self, value: typing.Optional[int], /) -> None:
        ...

    @abc.abstractmethod
    def append_entries(
        self,
        entries: typing.Sequence[domain_auditlog_entry.MigrationAuditlogEntry],
    ) -> None:
        ...

    @abc.abstractmethod
    def load_entries(
        self, limit: typing.Optional[int] = None
    ) -> typing.Sequence[domain_auditlog_entry.MigrationAuditlogEntry]:
        ...

    @abc.abstractmethod
    def history(
        self,
        start: typing.Optional[datetime.datetime] = None,
        end: typing.Optional[datetime.datetime] = None,
        limit: typing.Optional[int] = None,
        ascending_date: bool = True,
    ) -> typing.Iterator[domain_auditlog_entry.MigrationAuditlogEntry]:
        ...
