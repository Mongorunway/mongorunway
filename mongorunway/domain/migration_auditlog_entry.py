from __future__ import annotations

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
    migration: domain_migration.MigrationReadModel
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
