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
"""The module contains an interface for a database migration audit log that allows recording
completed database migrations and retrieving information about the migration history.
"""
from __future__ import annotations

__all__: typing.Sequence[str] = ("AuditlogJournal",)

import abc
import datetime
import typing

if typing.TYPE_CHECKING:
    from mongorunway.domain import migration_auditlog_entry as domain_auditlog_entry


class AuditlogJournal(abc.ABC):
    """The AuditlogJournal class is an interface to migration audit logs.
    It provides methods to record completed database migrations and retrieve
    information about the migration history. The class is used by the migration
    application to record completed database migrations and provide information
    about the migration history.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
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
        ...

    @abc.abstractmethod
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
        List[MigrationReadModel]
            A sequence of audit log entries from the journal.
        """
        ...

    @abc.abstractmethod
    def history(
        self,
        start: typing.Optional[datetime.datetime] = None,
        end: typing.Optional[datetime.datetime] = None,
        limit: typing.Optional[int] = None,
        ascending_date: bool = True,
    ) -> typing.Iterator[domain_auditlog_entry.MigrationAuditlogEntry]:
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
        MigrationReadModel
            An audit log entry within the specified time range.
        """
        ...
