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
"""This module contains services for querying migration objects."""
from __future__ import annotations

__all__: typing.Sequence[str] = ("MigrationQueryService",)

import typing

import pymongo

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.ui import MigrationUI
    from mongorunway.kernel.domain.migration import Migration


class MigrationQueryService:
    """Provides services to query pending migrations.

    Parameters
    ----------
    application : MigrationUI
        The migration UI to query for pending migrations.
    """

    __slots__: typing.Sequence[str] = ("_application",)

    def __init__(self, application: MigrationUI, /) -> None:
        self._application = application

    def get_pending_migrations(self, *, sort_by: int = pymongo.ASCENDING) -> typing.Sequence[Migration]:
        """Returns a sequence of all pending migrations, optionally sorted.

        Parameters
        ----------
        sort_by : int, optional
            The sort order of the migrations. Defaults to pymongo.ASCENDING.

        Returns
        -------
        typing.Sequence[Migration]
            A sequence of all pending migrations.
        """
        return self._application.pending.acquire_all_migrations(sort_by=sort_by)

    def get_pending_migrations_count(self) -> int:
        """Returns the count of pending migrations.

        Returns
        -------
        int
            The count of pending migrations.
        """
        return len(self._application.pending)

    def get_first_pending_migration(self) -> typing.Optional[Migration]:
        """Returns the first pending migration, or None if there are no pending migrations.

        Returns
        -------
        typing.Optional[Migration]
            The first pending migration, or None if there are no pending migrations.
        """
        return self._application.pending.acquire_first_migration()

    def get_latest_pending_migration(self) -> typing.Optional[Migration]:
        """Returns the latest pending migration, or None if there are no pending migrations.

        Returns
        -------
        typing.Optional[Migration]
            The latest pending migration, or None if there are no pending migrations.
        """
        return self._application.pending.acquire_latest_migration()

    def get_pending_waiting_migration(self) -> typing.Optional[Migration]:
        """Returns the next waiting migration, or None if there are no waiting migrations.

        Returns
        -------
        typing.Optional[Migration]
            The next waiting migration, or None if there are no waiting migrations.
        """
        return self._application.pending.acquire_waiting_migration()

    def get_applied_migrations(self, *, sort_by: int = pymongo.ASCENDING) -> typing.Sequence[Migration]:
        """Returns a sequence of Migration objects representing all the applied migrations.

        Parameters
        ----------
        sort_by : int, optional
            The order in which the migrations should be sorted. Default is pymongo.ASCENDING.

        Returns
        -------
        typing.Sequence[Migration]
            A sequence of Migration objects representing all the applied migrations.
        """
        return self._application.applied.acquire_all_migrations(sort_by=sort_by)

    def get_applied_migrations_count(self) -> int:
        """Return the number of migrations that have been applied.

        Returns
        -------
        int
            The number of applied migrations.
        """
        return len(self._application.applied)

    def get_first_applied_migration(self) -> typing.Optional[Migration]:
        """Get the first applied migration.

        Returns
        -------
        typing.Optional[Migration]
            The first applied migration or None if there are no applied migrations.
        """
        return self._application.applied.acquire_first_migration()

    def get_latest_applied_migration(self) -> typing.Optional[Migration]:
        """Retrieve the latest applied migration in the database.

        Returns
        -------
        typing.Optional[Migration]
            The latest applied migration or None if no migrations have been applied.
        """
        return self._application.applied.acquire_latest_migration()

    def get_applied_waiting_migration(self) -> typing.Optional[Migration]:
        """Retrieve the next migration that is waiting to be applied.

        Returns
        -------
        typing.Optional[Migration]
            An instance of Migration or None if there are no pending migrations.
        """
        return self._application.applied.acquire_waiting_migration()

    def get_migrations_count(self) -> int:
        """Get the total count of migrations, both applied and pending.

        Returns
        -------
        int
            The total count of migrations.

        Notes
        -----
        This method returns the sum of the counts returned by the `get_pending_migrations_count`
        and `get_applied_migrations_count` methods.
        """
        return self.get_pending_migrations_count() + self.get_applied_migrations_count()
