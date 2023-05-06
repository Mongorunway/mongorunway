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
"""The module contains implementations of the audit log migration record models."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "EntryTypeRegistry",
    "entry_registry",
    "AuditlogEntry",
    "MigrationUpgraded",
    "MigrationDowngraded",
    "BulkMigrationUpgraded",
    "BulkMigrationDowngraded",
    "PendingMigrationAdded",
    "PendingMigrationRemoved",
)

import dataclasses
import datetime
import typing
import zoneinfo

from mongorunway.kernel.domain.migration import MigrationReadModel

T = typing.TypeVar("T")
EntryTT = typing.TypeVar("EntryTT", bound=typing.Type["AuditlogEntry"])


class EntryTypeRegistry:
    __slots__: typing.Sequence[str] = ("_registered_entries",)

    def __init__(self) -> None:
        self._registered_entries: typing.Dict[str, typing.Type[AuditlogEntry]] = {}

    def register(self, entry_cls: EntryTT, /) -> EntryTT:
        self._registered_entries[entry_cls.__name__] = entry_cls
        return entry_cls

    def get_entry_type(self, entry_name: str, /) -> typing.Optional[typing.Type[AuditlogEntry]]:
        return self._registered_entries.get(entry_name)


entry_registry = EntryTypeRegistry()


class AuditlogEntry:
    def __init__(self, *, name: str, date: datetime.datetime = datetime.datetime.utcnow()) -> None:
        self.name = name
        self.date = date

    @classmethod
    def new(cls, *args: typing.Any, **kwargs: typing.Any) -> AuditlogEntry:
        return cls(name=cls.__name__, *args, **kwargs)

    @classmethod
    def from_schema(cls: typing.Type[EntryTT], mapping: typing.Dict[str, typing.Any], /) -> T:
        mapping.pop("_id", None)
        return cls(**mapping)

    def with_time_zone(self, timezone: str, /) -> typing.Self:
        if timezone != "UTC":
            # Default time is utc
            try:
                self.date = self.date.astimezone(zoneinfo.ZoneInfo(timezone))
            except zoneinfo.ZoneInfoNotFoundError as exc:
                raise ModuleNotFoundError(
                    "You need install 'tzdata' module to use timezones in auditlog journals"
                ) from exc

        return self

    def schema(self) -> typing.Dict[str, typing.Any]:
        mapping = self.__dict__.copy()
        return mapping


@entry_registry.register
class MigrationUpgraded(AuditlogEntry):
    def __init__(
        self,
        *,
        name: str,
        upgraded_count: int,
        migration_read_model: MigrationReadModel,
        date: datetime.datetime = datetime.datetime.utcnow(),
    ) -> None:
        super().__init__(name=name, date=date)
        self.migration_read_model = migration_read_model
        self.upgraded_count = upgraded_count

    @classmethod
    def from_schema(cls: typing.Type[T], mapping: typing.Dict[str, typing.Any], /) -> T:
        mapping["migration_read_model"] = MigrationReadModel.from_dict(mapping["migration_read_model"])
        return super().from_schema(mapping)

    def schema(self) -> typing.Dict[str, typing.Any]:
        mapping = super().schema()
        mapping["migration_read_model"] = dataclasses.asdict(self.migration_read_model)
        return mapping


@entry_registry.register
class PendingMigrationAdded(AuditlogEntry):
    def __init__(
        self,
        *,
        name: str,
        migration_read_model: MigrationReadModel,
        date: datetime.datetime = datetime.datetime.utcnow(),
    ) -> None:
        super().__init__(name=name, date=date)
        self.migration_read_model = migration_read_model

    @classmethod
    def from_schema(cls: typing.Type[T], mapping: typing.Dict[str, typing.Any], /) -> T:
        mapping["migration_read_model"] = MigrationReadModel.from_dict(mapping["migration_read_model"])
        return super().from_schema(mapping)

    def schema(self) -> typing.Dict[str, typing.Any]:
        mapping = super().schema()
        mapping["migration_read_model"] = dataclasses.asdict(self.migration_read_model)
        return mapping


@entry_registry.register
class PendingMigrationRemoved(AuditlogEntry):
    def __init__(
        self,
        *,
        name: str,
        migration_read_model: MigrationReadModel,
        date: datetime.datetime = datetime.datetime.utcnow(),
    ) -> None:
        super().__init__(name=name, date=date)
        self.migration_read_model = migration_read_model

    @classmethod
    def from_schema(cls: typing.Type[T], mapping: typing.Dict[str, typing.Any], /) -> T:
        mapping["migration_read_model"] = MigrationReadModel.from_dict(mapping["migration_read_model"])
        return super().from_schema(mapping)

    def schema(self) -> typing.Dict[str, typing.Any]:
        mapping = super().schema()
        mapping["migration_read_model"] = dataclasses.asdict(self.migration_read_model)
        return mapping


@entry_registry.register
class MigrationDowngraded(AuditlogEntry):
    def __init__(
        self,
        *,
        name: str,
        downgraded_count: int,
        migration_read_model: MigrationReadModel,
        date: datetime.datetime = datetime.datetime.utcnow(),
    ) -> None:
        super().__init__(name=name, date=date)
        self.migration_read_model = migration_read_model
        self.downgraded_count = downgraded_count

    @classmethod
    def from_schema(cls: typing.Type[T], mapping: typing.Dict[str, typing.Any], /) -> T:
        mapping["migration_read_model"] = MigrationReadModel.from_dict(mapping["migration_read_model"])
        return super().from_schema(mapping)

    def schema(self) -> typing.Dict[str, typing.Any]:
        mapping = super().schema()
        mapping["migration_read_model"] = dataclasses.asdict(self.migration_read_model)
        return mapping


@entry_registry.register
class BulkMigrationUpgraded(AuditlogEntry):
    def __init__(
        self,
        *,
        name: str,
        upgraded_count: int,
        upgraded_migrations: typing.Sequence[MigrationReadModel],
        date: datetime.datetime = datetime.datetime.utcnow(),
    ) -> None:
        super().__init__(name=name, date=date)
        self.upgraded_migrations = upgraded_migrations
        self.upgraded_count = upgraded_count

    @classmethod
    def from_schema(cls: typing.Type[T], mapping: typing.Dict[str, typing.Any], /) -> T:
        mapping["upgraded_migrations"] = [
            MigrationReadModel.from_dict(schema) for schema in mapping["upgraded_migrations"]
        ]
        return super().from_schema(mapping)

    def schema(self) -> typing.Dict[str, typing.Any]:
        mapping = super().schema()
        mapping["upgraded_migrations"] = [
            dataclasses.asdict(read_model) for read_model in mapping["upgraded_migrations"]
        ]
        return mapping


@entry_registry.register
class BulkMigrationDowngraded(AuditlogEntry):
    def __init__(
        self,
        *,
        name: str,
        downgraded_count: int,
        downgraded_migrations: typing.Sequence[MigrationReadModel],
        date: datetime.datetime = datetime.datetime.utcnow(),
    ) -> None:
        super().__init__(name=name, date=date)
        self.downgraded_migrations = downgraded_migrations
        self.downgraded_count = downgraded_count

    @classmethod
    def from_schema(cls: typing.Type[T], mapping: typing.Dict[str, typing.Any], /) -> T:
        mapping["downgraded_migrations"] = [
            MigrationReadModel.from_dict(schema) for schema in mapping["downgraded_migrations"]
        ]
        return super().from_schema(mapping)

    def schema(self) -> typing.Dict[str, typing.Any]:
        mapping = super().schema()
        mapping["downgraded_migrations"] = [
            dataclasses.asdict(schema) for schema in mapping["downgraded_migrations"]
        ]
        return mapping
