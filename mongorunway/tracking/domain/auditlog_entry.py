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
    "MigrationFileTemplateCreated",
)

import dataclasses
import datetime
import typing
import zoneinfo

from mongorunway.kernel.domain.migration import MigrationReadModel

T = typing.TypeVar("T")


class EntryTypeRegistry:
    __slots__: typing.Sequence[str] = ("_registered_entries",)

    def __init__(self) -> None:
        self._registered_entries = {}

    def register(self, entry_cls: T, /) -> T:
        self._registered_entries[entry_cls.__name__] = entry_cls
        return entry_cls

    def get_entry_type(self, entry_name: str, /) -> typing.Optional[AuditlogEntry]:
        return self._registered_entries.get(entry_name)


entry_registry = EntryTypeRegistry()


class AuditlogEntry:
    __slots__: typing.Sequence[str] = (
        "name",
        "date",
    )

    def __init__(self, *, name: str, date: datetime.datetime = datetime.datetime.utcnow()) -> None:
        self.name = name
        self.date = date

    @classmethod
    def new(cls, *args, **kwargs) -> AuditlogEntry:
        return cls(name=cls.__name__, *args, **kwargs)

    @classmethod
    def from_schema(cls: typing.Type[T], mapping: typing.Dict[str, typing.Any], /) -> T:
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
    __slots__: typing.Sequence[str] = (
        "upgraded_count",
        "migration_read_model",
    )

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
    __slots__: typing.Sequence[str] = ("migration_read_model",)

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
    __slots__: typing.Sequence[str] = ("migration_read_model",)

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
    __slots__: typing.Sequence[str] = (
        "downgraded_count",
        "migration_read_model",
    )

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
    __slots__: typing.Sequence[str] = (
        "upgraded_count",
        "upgraded_migrations",
    )

    def __init__(
        self,
        *,
        name: str,
        upgraded_count: int,
        upgraded_migrations: typing.Sequence[int],
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
    __slots__: typing.Sequence[str] = (
        "downgraded_count",
        "downgraded_migrations",
    )

    def __init__(
        self,
        *,
        name: str,
        downgraded_count: int,
        downgraded_migrations: typing.Sequence[int],
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


@entry_registry.register
class MigrationFileTemplateCreated(AuditlogEntry):
    __slots__: typing.Sequence[str] = (
        "migration_filename",
        "migration_version",
    )

    def __init__(
        self,
        *,
        name: str,
        migration_filename: str,
        migration_version: int,
        date: datetime.datetime = datetime.datetime.utcnow(),
    ) -> None:
        super().__init__(name=name, date=date)
        self.migration_filename = migration_filename
        self.migration_version = migration_version
