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
"""The transaction module provides classes for performing transactions in a migration application.
It contains implementations of the base transaction class as well as classes for different types of
transactions.
"""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "MigrationTransaction",
    "UpgradeTransaction",
    "DowngradeTransaction",
    "TRANSACTION_SUCCESS",
    "TRANSACTION_NOT_APPLIED",
)

import abc
import typing

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.ui import MigrationUI
    from mongorunway.kernel.domain.migration import Migration

TRANSACTION_SUCCESS = 1
"""An integer constant indicating that a transaction has been successfully applied."""

TRANSACTION_NOT_APPLIED = 0
"""An integer constant indicating that a transaction has not been applied."""


class MigrationTransaction(abc.ABC):
    """Abstract base class for implementing migration transactions."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def apply_migration(self, migration: Migration, /) -> None:
        """
        Apply the given migration to the database.

        Parameters
        ----------
        migration : Migration
            The migration to apply.
        """
        ...

    @abc.abstractmethod
    def commit(self) -> None:
        """Commit the transaction."""
        ...

    @abc.abstractmethod
    def rollback(self) -> None:
        """Rollback the transaction."""
        ...


class UpgradeTransaction(MigrationTransaction):
    """Represents a transaction for upgrading a migration.

    Parameters
    ----------
    application: MigrationUI
        The migration user interface.
    """

    __slots__: typing.Sequence[str] = ("_application", "_ctx_migration")

    def __init__(self, application: MigrationUI, /) -> None:
        self._application = application
        self._ctx_migration: typing.Optional[Migration] = None

    def apply_migration(self, migration: Migration, /) -> None:
        """Apply the given migration for upgrade.

        Parameters
        ----------
        migration: Migration
            The migration to upgrade.
        """
        self._ctx_migration = migration
        migration.upgrade(self._application.config.connection.mongo_client)

    def commit(self) -> None:
        """
        Commit the transaction by appending the applied migration and removing the
        pending migration.
        """
        waiting_migration = self._ensure_migration()
        self._application.applied.append_migration(waiting_migration)
        self._application.pending.remove_migration(waiting_migration.version)

    def rollback(self) -> None:
        """
        Rollback the transaction by removing the applied migration and adding the pending
        migration back.
        """
        waiting_migration = self._ensure_migration()

        if self._application.applied.has_migration(waiting_migration):
            self._application.applied.remove_migration(waiting_migration.version)

        if not self._application.pending.has_migration(waiting_migration):
            self._application.pending.append_migration(waiting_migration)

    def _ensure_migration(self) -> Migration:
        """Ensure that the current migration being upgraded is not None.

        Returns
        -------
        Migration
            The current migration being upgraded.

        Raises
        ------
        ValueError
            If the current migration being upgraded is None.
        """
        if self._ctx_migration is None:
            raise ValueError("Migration is not upgraded.")

        return self._ctx_migration


class DowngradeTransaction(MigrationTransaction):
    """Represents a downgrade transaction for a migration application.

    Parameters:
    -----------
    application: MigrationUI
        The migration application.
    """

    __slots__: typing.Sequence[str] = ("_application", "_ctx_migration")

    def __init__(self, application: MigrationUI, /) -> None:
        self._application = application
        self._ctx_migration: typing.Optional[Migration] = None

    def apply_migration(self, migration: Migration, /) -> None:
        """Apply the migration.

        Parameters:
        -----------
        migration: Migration
            The migration to apply.
        """
        self._ctx_migration = migration
        migration.downgrade(self._application.config.connection.mongo_client)

    def commit(self) -> None:
        """
        Commit the transaction by appending the pending migration and removing the
        applied migration.
        """
        waiting_migration = self._ensure_migration()
        self._application.pending.append_migration(waiting_migration)
        self._application.applied.remove_migration(waiting_migration.version)

    def rollback(self) -> None:
        """
        Rollback the transaction by removing the pending migration and adding the applied
        migration back.
        """
        waiting_migration = self._ensure_migration()

        if self._application.pending.has_migration(waiting_migration):
            self._application.pending.remove_migration(waiting_migration.version)

        if not self._application.applied.has_migration(waiting_migration):
            self._application.applied.append_migration(waiting_migration)

    def _ensure_migration(self) -> Migration:
        """Ensure that a migration is upgraded.

        Raises:
        -------
        ValueError
            If the migration is not upgraded.

        Returns:
        --------
        Migration
            The upgraded migration.
        """
        if self._ctx_migration is None:
            raise ValueError("Migration is not upgraded.")

        return self._ctx_migration
