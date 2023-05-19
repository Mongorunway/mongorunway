from __future__ import annotations

import abc
import typing

if typing.TYPE_CHECKING:
    from mongorunway.application import session
    from mongorunway.domain import migration as domain_migration


class MigrationSessionAware(abc.ABC):
    @property
    @abc.abstractmethod
    def session(self) -> session.MigrationSession:
        """Return the session of the migration app.

        Returns
        -------
        ApplicationSession
            The session of the migration app.
        """
        ...


class MigrationRunner(abc.ABC):
    __slots__ = ()

    @abc.abstractmethod
    def upgrade_once(self) -> int:
        """Apply a single pending migration and commit the changes to the database.

        Returns
        -------
        int
            An integer indicating the success or failure of the upgrade transaction.

        Raises
        ------
        NothingToUpgradeError
            If there are no pending migrations.
        """
        ...

    @abc.abstractmethod
    def downgrade_once(self) -> int:
        """Revert the most recently applied migration and commit the changes to the database.

        Returns
        -------
        int
            An integer indicating the success or failure of the downgrade transaction.

        Raises
        ------
        NothingToDowngradeError:
            If there are no applied migrations.
        """
        ...

    @abc.abstractmethod
    def upgrade_while(
        self, predicate: typing.Callable[[domain_migration.Migration], bool], /
    ) -> int:
        """Apply pending migrations until a certain condition is met and commit the
        changes to the database.

        Parameters
        ----------
        predicate : Callable[[Migration], bool]
            A callable object that takes a Migration object as an argument and returns a
            boolean value. The predicate is used to determine when to stop applying migrations.

        Returns
        -------
        int
            The number of migrations that were successfully applied.

        Raises
        ------
        NothingToUpgradeError
            If there are no pending migrations.
        """
        ...

    @abc.abstractmethod
    def downgrade_while(
        self, predicate: typing.Callable[[domain_migration.Migration], bool], /
    ) -> int:
        """Downgrade applied migrations while the given predicate function is true.

        Parameters
        ----------
        predicate : Callable[[Migration], bool]
            A callable object that accepts a single argument of type Migration and
            returns a boolean. This predicate function is used to determine whether
            to continue downgrading the next migration or not.

        Returns
        -------
        int
            The number of migrations that have been downgraded.

        Raises
        ------
        NothingToDowngradeError:
            If there are no applied migrations.
        """
        ...

    @abc.abstractmethod
    def downgrade_to(self, migration_version: int, /) -> int:
        """Downgrades the database to the specified migration version.

        Parameters
        ----------
        migration_version : int
            The migration version to which the database should be downgraded.

        Returns
        -------
        int
            The number of migrations successfully downgraded.

        Raises
        ------
        NothingToDowngradeError
            If there are no applied migrations.
        ValueError
            If the specified migration version is not found in the applied migrations.
        """
        ...

    @abc.abstractmethod
    def upgrade_to(self, migration_version: int, /) -> int:
        """Upgrades the database to the specified migration version.

        Parameters
        ----------
        migration_version : int
            The migration version to which the database should be upgraded.

        Returns
        -------
        int
            The number of migrations successfully upgraded.

        Raises
        ------
        NothingToUpgradeError
            If there are no pending migrations.
        ValueError
            If the specified migration version is not found in the pending migrations.
        """
        ...

    @abc.abstractmethod
    def downgrade_all(self) -> int:
        """Downgrades the database by undoing all previously applied migrations.

        Returns
        -------
        int
            The number of migrations successfully downgraded.

        Raises
        ------
        NothingToDowngradeError
            If there are no applied migrations.
        """
        ...

    @abc.abstractmethod
    def upgrade_all(self) -> int:
        """Upgrades the database by applying all pending migrations.

        Returns
        -------
        int
            The number of migrations successfully upgraded.

        Raises
        ------
        NothingToUpgradeError
            If there are no pending migrations.
        """
        ...
