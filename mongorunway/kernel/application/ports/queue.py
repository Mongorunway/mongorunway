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
"""This module defines the MigrationQueue interface for managing a queue of Migration objects.
It defines a set of abstract methods that must be implemented by any class that implements the
MigrationQueue interface.
"""
from __future__ import annotations

__all__: typing.Sequence[str] = ("MigrationQueue",)

import abc
import typing

import pymongo

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration import Migration


class MigrationQueue(abc.ABC):
    """The MigrationQueue interface is designed to be used with a database that stores migration records.
    It provides methods for acquiring, appending, and removing migration records, as well as querying
    the state of the queue.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def sort_order(self) -> int:
        """Get the sorting order of the migration documents in the database.

        Returns
        -------
        int
            An integer that indicates the sorting order of the migration documents
            in the database. This value is either pymongo.ASCENDING or pymongo.DESCENDING.
        """
        ...

    @abc.abstractmethod
    def __len__(self) -> int:
        """Return the number of migration documents in the queue.

        Returns
        -------
        int
            The number of migration documents in the queue.
        """
        ...

    @abc.abstractmethod
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
        """
        ...

    @abc.abstractmethod
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
        """
        ...

    @abc.abstractmethod
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
        """
        ...

    @abc.abstractmethod
    def has_migrations(self) -> bool:
        """Return True if there are any migration documents in the queue.

        Returns
        -------
        bool
            True if there are any migration documents in the queue, False
            otherwise.
        """
        ...

    @abc.abstractmethod
    def acquire_waiting_migration(self) -> typing.Optional[Migration]:
        """Acquires waiting migration from the collection and returns it as a Migration object,
        or returns None if there are no waiting migrations.

        Returns
        -------
        typing.Optional[Migration]
            A Migration object representing the acquired migration or None if no migration is
            available.
        """
        ...

    @abc.abstractmethod
    def pop_waiting_migration(self) -> typing.Optional[Migration]:
        """Atomically removes and returns the next waiting migration from the collection.
        If there are no waiting migrations, returns None.

        Returns:
        -------
        Optional[Migration]
            The next waiting migration, or None if no waiting migrations exist.
        """
        ...

    @abc.abstractmethod
    def acquire_first_migration(self) -> typing.Optional[Migration]:
        """Acquire the first migration in the collection according to its version in ascending order.

        Returns
        -------
        typing.Optional[Migration]
            The first Migration object in the collection, or None if the collection is empty.
        """
        ...

    @abc.abstractmethod
    def acquire_latest_migration(self) -> typing.Optional[Migration]:
        """Acquire the latest migration from the collection according to its version in descending order.

        Returns
        -------
        typing.Optional[Migration]
            An optional Migration object if a migration is found, otherwise None.
        """
        ...

    @abc.abstractmethod
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
        """
        ...

    @abc.abstractmethod
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
        """
        ...

    @abc.abstractmethod
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
        """
        ...

    @abc.abstractmethod
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
        """
        ...
