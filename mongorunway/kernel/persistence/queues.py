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
"""This module provides implementations of the `MigrationQueue` interface."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "BaseMigrationQueue",
    "AppliedMigrationQueue",
    "PendingMigrationQueue",
)

import threading
import typing

import pymongo

from mongorunway.kernel.application.ports.queue import MigrationQueue
from mongorunway.kernel.domain.migration import Migration
from mongorunway.kernel.infrastructure.migrations import BaseMigration

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.ui import MigrationUI


class BaseMigrationQueue(MigrationQueue):
    """The `BaseMigrationQueue` class is a base class that implements
    the MigrationQueue interface. It provides a skeleton implementation of the
    interface methods and additional methods for managing migration queues.

    Parameters
    ----------
    application: MigrationUI
        An instance of the MigrationUI class that provides a user interface for
        managing migrations.
    sort_order: int
        An integer that indicates the sorting order of the migration documents in
        the database.
        This value must be either pymongo.ASCENDING or pymongo.DESCENDING.
    collection: Collection[typing.Dict[str, typing.Any]]
        A MongoDB collection that stores the migration documents.

    Raises
    ------
    ValueError
        If an unsupported sort_order is specified.
    """

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
        if sort_order not in (pymongo.ASCENDING, pymongo.DESCENDING):
            raise ValueError(f"Unsupported sort order: {self._sort_order}")

        self._application = application
        self._collection = collection
        self._sort_order = sort_order
        self._lock = threading.RLock()  # Use reentrant lock to allow nested acquire/release

    @property
    def sort_order(self) -> int:
        """Get the sorting order of the migration documents in the database.

        Returns
        -------
        int
            An integer that indicates the sorting order of the migration documents
            in the database. This value is either pymongo.ASCENDING or pymongo.DESCENDING.
        """
        return self._sort_order

    def __len__(self) -> int:
        """Return the number of migration documents in the queue.

        Returns
        -------
        int
            The number of migration documents in the queue.

        Notes
        -----
        This method is thread-safe and uses a reentrant lock to prevent race conditions when
        accessing the queue.
        """
        with self._lock:
            return self._collection.count_documents({})

    def __contains__(self, item: typing.Any, /) -> bool:
        """Return True if the specified migration object is in the queue, False otherwise.

        Parameters
        ----------
        item : Any
            The migration object to search for in the queue.

        Returns
        -------
        bool
            True if the migration object is in the queue, False otherwise.

        Notes
        -----
        This method is thread-safe and uses a reentrant lock to prevent race conditions when
        accessing the queue.
        """
        if not isinstance(item, Migration):
            return NotImplemented

        with self._lock:
            return self.has_migration(item)

    def has_migration(self, migration: Migration, /) -> bool:
        """Return True if a migration with the given version is in the queue, False otherwise.

        Parameters
        ----------
        migration : Migration
            The migration object to check for.

        Returns
        -------
        bool
            True if the migration is in the queue, False otherwise.

        Raises
        ------
        TypeError
            If the given migration is not an instance of the Migration class.

        Notes
        -----
        This method is thread-safe and uses a reentrant lock to prevent race conditions when
        accessing the queue.
        """
        if not isinstance(migration, Migration):
            raise TypeError(f"Item must be instance of {Migration!r}.")

        with self._lock:
            return self.has_migration_with_version(migration.version)

    def has_migration_with_version(self, migration_version, /) -> bool:
        """Checks if a migration with the given version number exists in the migration queue.

        Parameters
        ----------
        migration_version: int
            The version number of the migration to check.

        Returns
        -------
        bool
            True if a migration with the given version number exists in the queue, False otherwise.

        Raises
        ------
        TypeError
            If the `migration_version` parameter is not an integer.

        Notes
        -----
        This method is thread-safe and uses a reentrant lock to prevent race conditions when
        accessing the queue.
        """
        if not isinstance(migration_version, int):
            raise TypeError(f"Item must be instance of {int!r}.")

        with self._lock:
            return self._collection.count_documents({"_id": migration_version}) > 0

    def has_migrations(self) -> bool:
        """Return True if there are any migration documents in the queue.

        Returns
        -------
        bool
            True if there are any migration documents in the queue, False
            otherwise.

        Notes
        -----
        This method is thread-safe and uses a reentrant lock to prevent race conditions when
        accessing the queue.
        """
        with self._lock:
            return bool(self._collection.count_documents({}, limit=1))

    def acquire_migration(self, migration_version: int, /) -> typing.Optional[Migration]:
        """Acquire a Migration object with the given version number.

        Parameters
        ----------
        migration_version : int
            The version number of the migration to acquire.

        Returns
        -------
        Optional[Migration]
            The acquired Migration object with the specified version number, or None if it
            doesn't exist.

        Notes
        -----
        This method is thread-safe and uses a reentrant lock to prevent race conditions when
        accessing the queue.
        """
        with self._lock:
            migration_dict = self._collection.find_one({"_id": migration_version})

        if migration_dict is not None:
            return self._build_migration(migration_dict)

    def acquire_waiting_migration(self) -> typing.Optional[Migration]:
        """Acquires waiting migration from the collection and returns it as a Migration object,
        or returns None if there are no waiting migrations.

        Returns
        -------
        typing.Optional[Migration]
            A Migration object representing the acquired migration or None if no migration is
            available.

        Notes
        -----
        This method is thread-safe and uses a reentrant lock to prevent race conditions when
        accessing the queue.
        """
        with self._lock:
            migration_dict = self._collection.find_one(sort=[("version", self.sort_order)])

        if migration_dict is not None:
            return self._build_migration(migration_dict)

    def pop_waiting_migration(self) -> typing.Optional[Migration]:
        """Atomically removes and returns the next waiting migration from the collection.
        If there are no waiting migrations, returns None.

        Returns:
        -------
        Optional[Migration]
            The next waiting migration, or None if no waiting migrations exist.

        Notes
        -----
        This method is thread-safe and uses a reentrant lock to prevent race conditions when
        accessing the queue.
        """
        with self._lock:
            migration_dict = self._collection.find_one_and_delete({}, sort=[("version", self.sort_order)])

        if migration_dict is not None:
            return self._build_migration(migration_dict)

    def acquire_latest_migration(self) -> typing.Optional[Migration]:
        """Acquire the latest migration from the collection according to its version in descending order.

        Returns
        -------
        typing.Optional[Migration]
            An optional Migration object if a migration is found, otherwise None.

        Notes
        -----
        This method is thread-safe and uses a reentrant lock to prevent race conditions when
        accessing the queue.
        """
        with self._lock:
            migration_dict = self._collection.find_one(sort=[("version", pymongo.DESCENDING)])

        if migration_dict is not None:
            return self._build_migration(migration_dict)

    def acquire_first_migration(self) -> typing.Optional[Migration]:
        """Acquire the first migration in the collection according to its version in ascending order.

        Returns
        -------
        typing.Optional[Migration]
            The first Migration object in the collection, or None if the collection is empty.

        Notes
        -----
        This method is thread-safe and uses a reentrant lock to prevent race conditions when
        accessing the queue.
        """
        with self._lock:
            migration_dict = self._collection.find_one(sort=[("version", pymongo.ASCENDING)])

        if migration_dict is not None:
            return self._build_migration(migration_dict)

    def acquire_all_migrations(self, *, sort_by: int = pymongo.ASCENDING) -> typing.Sequence[Migration]:
        """Acquire all migrations in the collection.

        Parameters
        ----------
        sort_by : int, optional
            Sort order to use for the query. Default is pymongo.ASCENDING.

        Returns
        -------
        typing.Sequence[Migration]
            A sequence of Migration objects, ordered according to the `sort_by` parameter.

        Notes
        -----
        This method is thread-safe and uses a reentrant lock to prevent race conditions when
        accessing the queue.
        """
        with self._lock:
            return [
                self.acquire_migration(record["version"])
                for record in self._collection.find({}, sort=[("version", sort_by)])
            ]

    def append_migration(self, migration: Migration, /) -> int:
        """Appends the given migration to the collection and returns its version number.

        Parameters
        ----------
        migration : Migration
            The migration to be added to the collection.

        Returns
        -------
        int
            The version number of the added migration.

        Notes
        -----
        This method is thread-safe and uses a reentrant lock to prevent race conditions when
        accessing the queue.
        """
        with self._lock:
            migration_dict = migration.to_mongo_dict()
            self._collection.insert_one(migration_dict)

            return migration.version

    def remove_migration(self, migration_version: int, /) -> None:
        """Remove the migration with the specified version number.

        Parameters
        ----------
        migration_version : int
            The version number of the migration to remove.

        Raises
        ------
        TypeError
            If the `migration_version` is not an instance of `int`.

        Notes
        -----
        This method is thread-safe and uses a reentrant lock to prevent race conditions when
        accessing the queue.
        """
        if not isinstance(migration_version, int):
            raise TypeError(f"Migration version must be instance of {int!r}.")

        with self._lock:
            self._collection.delete_one({"_id": migration_version})

    def _build_migration(self, migration_dict: typing.Dict[str, typing.Any], /) -> typing.Optional[Migration]:
        current_migration_state = self._application.get_migration_from_filename(  # For commands
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
    """A migration queue implementation that tracks the applied migrations using a last-in-first-out
    (LIFO) algorithm.
    """
    def __init__(self, application: MigrationUI) -> None:
        super().__init__(
            application,
            sort_order=pymongo.DESCENDING,
            collection=application.config.connection.applied_migration_collection,
        )


class PendingMigrationQueue(BaseMigrationQueue):
    """A migration queue implementation that tracks the applied migrations using a first-in-first-out
    (FIFO) algorithm.
    """
    def __init__(self, application: MigrationUI) -> None:
        super().__init__(
            application,
            sort_order=pymongo.ASCENDING,
            collection=application.config.connection.pending_migration_collection,
        )
