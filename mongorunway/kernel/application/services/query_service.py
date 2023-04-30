from __future__ import annotations

__all__: typing.Sequence[str] = ("MigrationQueryService",)

import dataclasses
import typing

import pymongo

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.ui import MigrationUI
    from mongorunway.kernel.domain.migration import Migration


@dataclasses.dataclass
class MigrationAnalytic:
    pending_migrations: typing.Sequence[Migration]
    applied_migrations: typing.Sequence[Migration]
    last_applied_migration: typing.Optional[Migration]


class MigrationQueryService:
    __slots__: typing.Sequence[str] = ("_application",)

    def __init__(self, application: MigrationUI, /) -> None:
        self._application = application

    def get_pending_migrations(self, *, sort_by: int = pymongo.ASCENDING) -> typing.Sequence[Migration]:
        return self._application.pending.acquire_all_migrations(sort_by=sort_by)

    def get_pending_migrations_count(self) -> int:
        return len(self._application.pending)

    def get_first_pending_migration(self) -> typing.Optional[Migration]:
        return self._application.pending.acquire_first_migration()

    def get_latest_pending_migration(self) -> typing.Optional[Migration]:
        return self._application.pending.acquire_latest_migration()

    def get_pending_nowait_migration(self) -> typing.Optional[Migration]:
        return self._application.pending.acquire_nowait_migration()

    def get_applied_migrations(self, *, sort_by: int = pymongo.ASCENDING) -> typing.Sequence[Migration]:
        return self._application.applied.acquire_all_migrations(sort_by=sort_by)

    def get_applied_migrations_count(self) -> int:
        return len(self._application.applied)

    def get_first_applied_migration(self) -> typing.Optional[Migration]:
        return self._application.applied.acquire_first_migration()

    def get_latest_applied_migration(self) -> typing.Optional[Migration]:
        return self._application.applied.acquire_latest_migration()

    def get_pending_applied_migration(self) -> typing.Optional[Migration]:
        return self._application.applied.acquire_nowait_migration()

    def get_migrations_count(self) -> int:
        return self.get_pending_migrations_count() + self.get_applied_migrations_count()
