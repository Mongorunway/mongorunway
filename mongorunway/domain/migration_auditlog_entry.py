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

__all__: typing.Sequence[str] = ("MigrationAuditlogEntry",)

import dataclasses
import datetime
import typing
import zoneinfo

import bson.binary

if typing.TYPE_CHECKING:
    from mongorunway.domain import migration as domain_migration

_SelfT = typing.TypeVar("_SelfT", bound="MigrationAuditlogEntry")


@dataclasses.dataclass
class MigrationAuditlogEntry:
    session_id: bson.Binary
    transaction_name: str
    migration_read_model: domain_migration.MigrationReadModel
    date_fmt: str
    date: datetime.datetime = dataclasses.field(default_factory=datetime.datetime.utcnow)
    exc_name: typing.Optional[str] = None
    exc_message: typing.Optional[str] = None

    @classmethod
    def from_dict(
        cls, mapping: typing.MutableMapping[str, typing.Any], /
    ) -> MigrationAuditlogEntry:
        mapping.pop("_id", None)  # For mongo records
        return cls(**mapping)

    def is_failed(self) -> bool:
        return self.exc_name is not None or self.exc_message is not None

    def with_error(self: _SelfT, exc: BaseException, /) -> _SelfT:
        self.exc_name = type(exc).__name__
        self.exc_message = str(exc)

        return self

    def with_timezone(self: _SelfT, timezone: str) -> _SelfT:
        if timezone != "UTC":
            # Default time is utc
            try:
                self.date = self.date.astimezone(zoneinfo.ZoneInfo(timezone))
            except zoneinfo.ZoneInfoNotFoundError as exc:
                raise ModuleNotFoundError(
                    "'tzdata' module must be installed to use timezones in auditlog journals."
                ) from exc

        return self

    def format_date(self) -> str:
        return self.date.strftime(self.date_fmt)
