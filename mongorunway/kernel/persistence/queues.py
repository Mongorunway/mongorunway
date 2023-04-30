from __future__ import annotations

__all__: typing.Sequence[str] = (
    "BaseMigrationQueue",
    "AppliedMigrationQueue",
    "PendingMigrationQueue",
)

import abc
import threading
import typing

import pymongo

from mongorunway.kernel.application.ports.queue import MigrationQueue
from mongorunway.kernel.domain.migration import Migration
from mongorunway.kernel.infrastructure.migrations import BaseMigration

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.ui import MigrationUI


class BaseMigrationQueue(MigrationQueue, abc.ABC):
    __slots__: typing.Sequence[str] = (
        "_application",
        "_collection",
        "_sort_order",
        "_lock",
    )

    def __init__(
        self,
        application: MigrationUI,
        *,
        sort_order: int,
        collection: pymongo.collection.Collection[typing.Dict[str, typing.Any]],
    ) -> None:
        self._application = application
        self._collection = collection
        self._sort_order = sort_order
        self._lock = threading.RLock()  # Use reentrant lock to allow nested acquire/release

    def __len__(self) -> int:
        with self._lock:
            return self._collection.count_documents({})

    def __contains__(self, item: typing.Any, /) -> bool:
        if not isinstance(item, Migration):
            return NotImplemented

        with self._lock:
            return self.has_migration(item)

    def has_migration(self, migration: Migration, /) -> bool:
        with self._lock:
            return self._collection.count_documents({"_id": migration.version}) > 0

    def has_migrations(self) -> bool:
        with self._lock:
            return bool(self._collection.count_documents({}, limit=1))

    def has_migration_with_version(self, migration_version, /) -> bool:
        with self._lock:
            return self.acquire_migration(migration_version) is not None

    def acquire_migration(self, migration_version: int, /) -> typing.Optional[Migration]:
        with self._lock:
            migration_dict = self._collection.find_one({"_id": migration_version})

        if migration_dict is not None:
            return self._build_migration(migration_dict)

    def acquire_nowait_migration(self) -> typing.Optional[Migration]:
        with self._lock:
            migration_dict = self._collection.find_one(sort=[("version", self._sort_order)])

        if migration_dict is not None:
            return self._build_migration(migration_dict)

    def pop_nowait_migration(self) -> typing.Optional[Migration]:
        with self._lock:
            migration_dict = self._collection.find_one_and_delete({}, sort=[("version", self._sort_order)])

        if migration_dict is not None:
            return self._build_migration(migration_dict)

    def acquire_latest_migration(self) -> typing.Optional[Migration]:
        with self._lock:
            migration_dict = self._collection.find_one(sort=[("version", pymongo.DESCENDING)])

        if migration_dict is not None:
            return self._build_migration(migration_dict)

    def acquire_first_migration(self) -> typing.Optional[Migration]:
        with self._lock:
            migration_dict = self._collection.find_one(sort=[("version", pymongo.ASCENDING)])

        if migration_dict is not None:
            return self._build_migration(migration_dict)

    def acquire_all_migrations(self, *, sort_by: int = pymongo.ASCENDING) -> typing.Iterator[Migration]:
        with self._lock:
            return [
                self.acquire_migration(record["version"])
                for record in self._collection.find({}, sort=[("version", sort_by)])
            ]

    def append_migration(self, migration: Migration, /) -> int:
        with self._lock:
            migration_dict = migration.to_mongo_dict()
            self._collection.insert_one(migration_dict)

            return migration.version

    def remove_migration(self, migration_version: int, /) -> None:
        with self._lock:
            self._collection.delete_one({"_id": migration_version})

    def _build_migration(self, migration_dict: typing.Dict[str, typing.Any], /) -> typing.Optional[Migration]:
        current_migration_state = self._application.get_migration_from_filename(  # Migrations could change
            migration_dict["name"],
        )
        return BaseMigration(
            name=migration_dict["name"],
            version=migration_dict["version"],
            checksum=migration_dict["checksum"],
            description=migration_dict["description"],
            upgrade_commands=current_migration_state.upgrade_commands,
            downgrade_commands=current_migration_state.downgrade_commands,
        )


class AppliedMigrationQueue(BaseMigrationQueue):
    # FIFO
    def __init__(self, application: MigrationUI) -> None:
        super().__init__(
            application,
            sort_order=pymongo.DESCENDING,
            collection=application.config.connection.applied_migration_collection,
        )


class PendingMigrationQueue(BaseMigrationQueue):
    # LIFO
    def __init__(self, application: MigrationUI) -> None:
        super().__init__(
            application,
            sort_order=pymongo.ASCENDING,
            collection=application.config.connection.pending_migration_collection,
        )
