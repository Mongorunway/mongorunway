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
"""The module provides tools for database migrations to interact with the user."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "MigrationApp",
    "MigrationAppImpl",
)

import abc
import functools
import logging
import typing

from mongorunway.application import session
from mongorunway.application import traits
from mongorunway.application import transactions
from mongorunway.application import ux
from mongorunway.application.ports import hook as hook_port
from mongorunway.application.services import migration_service
from mongorunway.application.services import versioning_service
from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_exception as domain_exception

if typing.TYPE_CHECKING:
    from mongorunway.application import config
    from mongorunway.application.ports import auditlog_journal as auditlog_journal_port
    from mongorunway.application.ports import repository as repository_port

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("mongorunway.ui")
_P = typing.ParamSpec("_P")
_TransactionCodeT = typing.TypeVar("_TransactionCodeT", bound=transactions.TransactionCode)


def requires_migrations(
    *,
    is_applied: bool,
) -> typing.Callable[
    [typing.Callable[_P, _TransactionCodeT]], typing.Callable[_P, _TransactionCodeT]
]:
    def decorator(
        meth: typing.Callable[_P, _TransactionCodeT],
    ) -> typing.Callable[_P, _TransactionCodeT]:
        @functools.wraps(meth)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _TransactionCodeT:
            if not isinstance((self := args[0]), traits.MigrationSessionAware):
                raise ValueError(
                    f"'requires_migrations' can be applied only to "
                    f"{traits.MigrationSessionAware!r} objects."
                )

            models = self.session.get_migration_models_by_flag(is_applied=is_applied)
            if not models:
                if self.session.session_config.application.raise_on_transaction_failure:
                    if is_applied:
                        raise domain_exception.NothingToUpgradeError()
                    raise domain_exception.NothingToDowngradeError()

                return typing.cast(
                    _TransactionCodeT,
                    transactions.TRANSACTION_NOT_APPLIED,
                )
            return meth(*args, **kwargs)

        return wrapper

    return decorator


class MigrationApp(traits.MigrationRunner, traits.MigrationSessionAware, abc.ABC):
    """Provides an interface for working with migration classes and managing the migration
    mechanism.  It allows for applying and rolling back migrations, as well as working with
    the storage of migration information. The class provides methods for performing operations
    with migrations and interacting with other classes and objects related to migrations.
    """

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the name of the migration app.

        Returns
        -------
        str
            The name of the migration app.
        """
        ...


class MigrationAppImpl(MigrationApp):
    """A base class for implementing a migration UI.

    This class provides an implementation of the abstract `MigrationUI` class.
    It provides basic functionality for managing applied and pending migrations.

    Parameters
    ----------
    configuration : ApplicationConfig
        The configuration of the application.
    startup_hooks : Union[List[PrioritizedMigrationHook], List[MigrationHook]], optional
        The list of startup hooks to be triggered when the application starts.
    """

    __slots__: typing.Sequence[str] = (
        "_config",
        "_session",
        "_startup_hooks",
        "_migration_service",
    )

    def __init__(
        self,
        configuration: config.Config,
        repository: repository_port.MigrationRepository,
        auditlog_journal: typing.Optional[auditlog_journal_port.AuditlogJournal] = None,
        startup_hooks: typing.Optional[hook_port.MixedHookList] = None,
    ) -> None:
        ux.init_logging(configuration)
        ux.configure_migration_indexes(configuration)

        self._startup_hooks = startup_hooks

        self._session = app_session = session.MigrationSessionImpl(
            self,
            configuration,
            repository,
            auditlog_journal,
        )

        self._migration_service = migration_service.MigrationService(app_session)

        if startup_hooks is not None:
            _LOGGER.info(
                "%s startup hook(s) found, running...",
                len(startup_hooks),
            )
            self._session.trigger_hooks(startup_hooks)

    @property
    def name(self) -> str:
        """Return the name of the migration app.

        Returns
        -------
        str
            The name of the migration app.
        """
        return self._session.session_config.application.app_name

    @property
    def session(self) -> session.MigrationSession:
        """Return the session of the migration app.

        Returns
        -------
        ApplicationSession
            The session of the migration app.
        """
        return self._session

    @requires_migrations(is_applied=False)
    def upgrade_once(self) -> int:
        """Apply a single pending migration and commit the changes to the database.

        Returns
        -------
        int
            An integer indicating the success or failure of the upgrade transaction.

        Raises
        ------
        NothingToUpgradeError
            If there are no pending migrations and raise_if_nothing_happens is True in the
            runtime configuration.
        """
        pending_migration_model = self._session.get_migration_model_by_flag(is_applied=False)
        assert pending_migration_model is not None  # Only for type checkers

        pending_migration = self._migration_service.get_migration_from_filename(
            pending_migration_model.name
        )

        _LOGGER.info(
            "%s: upgrading waiting migration (#%s -> #%s)...",
            self.name,
            versioning_service.get_previous_migration_version(pending_migration),
            pending_migration.version,
        )

        with self._session.begin_transaction(transactions.UpgradeTransaction) as transaction:
            transaction.apply(pending_migration)

            _LOGGER.info(
                "%s: Successfully upgraded to (#%s).",
                self.name,
                pending_migration.version,
            )
            return transactions.TRANSACTION_SUCCESS

    @requires_migrations(is_applied=True)
    def downgrade_once(self) -> int:
        """Revert the most recently applied migration and commit the changes to the database.

        Returns
        -------
        int
            An integer indicating the success or failure of the downgrade transaction.

        Raises
        ------
        NothingToDowngradeError:
            If there are no applied migrations and `raise_if_nothing_happens` configuration
            parameter is True.
        """
        applied_migration_model = self._session.get_migration_model_by_flag(is_applied=True)
        assert applied_migration_model is not None  # Only for type checkers

        applied_migration = self._migration_service.get_migration_from_filename(
            applied_migration_model.name
        )

        _LOGGER.info(
            "%s: downgrading waiting migration (#%s -> #%s)...",
            self.name,
            applied_migration.version,
            versioning_service.get_previous_migration_version(applied_migration),
        )

        with self._session.begin_transaction(transactions.DowngradeTransaction) as transaction:
            transaction.apply(applied_migration)

            _LOGGER.info(
                "%s: successfully downgraded to (#%s).",
                self.name,
                versioning_service.get_previous_migration_version(applied_migration),
            )
            return transactions.TRANSACTION_SUCCESS

    @requires_migrations(is_applied=False)
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
            If there are no pending migrations and raise_if_nothing_happens is True in the
            runtime configuration.

        Notes
        -----
        This method applies pending migrations until a certain condition is met.
        """
        upgraded = 0
        pending_migration_models = self._session.get_migration_models_by_flag(is_applied=False)

        while pending_migration_models:
            migration = self._migration_service.get_migration_from_filename(
                pending_migration_models.pop(0).name
            )

            if not predicate(migration):
                break

            _LOGGER.info(
                "%s: upgrading waiting migration (#%s -> #%s)...",
                self.name,
                versioning_service.get_previous_migration_version(migration),
                migration.version,
            )

            with self._session.begin_transaction(transactions.UpgradeTransaction) as transaction:
                transaction.apply(migration)

            _LOGGER.info(
                "%s: Successfully upgraded to (#%s).",
                self.name,
                migration.version,
            )
            upgraded += 1

        return upgraded

    @requires_migrations(is_applied=True)
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
            If there are no applied migrations and `raise_if_nothing_happens` configuration
            parameter is True.

        Notes
        -----
        If the predicate function returns False for a migration, the method stops downgrading
        and returns the number of migrations that have been successfully downgraded.
        """
        downgraded = 0
        applied_migration_models = self._session.get_migration_models_by_flag(is_applied=True)

        while applied_migration_models:
            migration = self._migration_service.get_migration_from_filename(
                applied_migration_models.pop(0).name
            )

            if not predicate(migration):
                break

            _LOGGER.info(
                "%s: downgrading waiting migration (#%s -> #%s)...",
                self.name,
                migration.version,
                versioning_service.get_previous_migration_version(migration),
            )

            with self._session.begin_transaction(transactions.DowngradeTransaction) as transaction:
                transaction.apply(migration)

            _LOGGER.info(
                "%s: successfully downgraded to (#%s).",
                self.name,
                versioning_service.get_previous_migration_version(migration),
            )
            downgraded += 1

        return downgraded

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
            If there are no applied migrations and `raise_if_nothing_happens` configuration
            parameter is True.
        ValueError
            If the specified migration version is not found in the applied migrations.

        Notes
        -----
        If the `migration_version` argument is `0`, the method will call `downgrade_all()`
        method which downgrades all applied migrations.
        """
        if not migration_version:
            return self.downgrade_all()

        model = self.session.get_migration_model_by_version(migration_version)
        if model is None:
            raise ValueError(f"Migration with version {migration_version!r} is not found.")

        if not model.is_applied:
            raise ValueError(f"Migration with version {migration_version} is already pending.")

        return self.downgrade_while(lambda m: m.version > migration_version)

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
            If there are no pending migrations and raise_if_nothing_happens is True in the
            runtime configuration.
        ValueError
            If the specified migration version is not found in the pending migrations.
        """
        model = self.session.get_migration_model_by_version(migration_version)
        if model is None:
            raise ValueError(f"Migration with version {migration_version!r} is not found.")

        if model.is_applied:
            raise ValueError(f"Migration with version {migration_version} is already applied.")

        return self.upgrade_while(lambda m: m.version <= migration_version)

    def downgrade_all(self) -> int:
        """Downgrades the database by undoing all previously applied migrations.

        Returns
        -------
        int
            The number of migrations successfully downgraded.

        Raises
        ------
        NothingToDowngradeError
            If there are no applied migrations and `raise_if_nothing_happens` configuration
            parameter is True.
        """
        return self.downgrade_while(lambda _: True)

    def upgrade_all(self) -> int:
        """Upgrades the database by applying all pending migrations.

        Returns
        -------
        int
            The number of migrations successfully upgraded.

        Raises
        ------
        NothingToUpgradeError
            If there are no pending migrations and raise_if_nothing_happens is True in the
            runtime configuration.
        """
        return self.upgrade_while(lambda _: True)
