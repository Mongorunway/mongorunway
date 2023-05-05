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
    "MigrationUI",
    "BaseMigrationUI",
    "ApplicationSession",
    "requires_pending_migration",
    "requires_applied_migration",
)

import abc
import contextlib
import functools
import heapq
import logging
import operator
import os
import typing

from mongorunway.kernel import util
from mongorunway.kernel.application.config import migration_file_template
from mongorunway.kernel.application.ports.hook import PrioritizedMigrationHook
from mongorunway.kernel.application.services.checksum_service import (
    calculate_migration_checksum,
)
from mongorunway.kernel.application.services.versioning_service import (
    get_previous_version,
)
from mongorunway.kernel.application.transactions import (
    TRANSACTION_NOT_APPLIED,
    TRANSACTION_SUCCESS,
    DowngradeTransaction,
    MigrationTransaction,
    UpgradeTransaction,
)
from mongorunway.kernel.domain.migration_exception import (
    MigrationTransactionFailedError,
    NothingToDowngradeError,
    NothingToUpgradeError,
)
from mongorunway.kernel.domain.migration_module import MigrationModule
from mongorunway.kernel.infrastructure.migrations import BaseMigration
from mongorunway.kernel.persistence.queues import (
    AppliedMigrationQueue,
    PendingMigrationQueue,
)

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.config import ApplicationConfig
    from mongorunway.kernel.application.ports.hook import MigrationHook
    from mongorunway.kernel.application.ports.queue import MigrationQueue
    from mongorunway.kernel.domain.migration import Migration

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("mongorunway.ui")

MP = typing.ParamSpec("MP")  # Migration paramspec
TransactionT = typing.TypeVar("TransactionT", bound=MigrationTransaction)


def requires_pending_migration(meth: typing.Callable[MP, int], /) -> typing.Callable[MP, int]:
    """The requires_pending_migration function is a decorator that can be applied
    to a method in the MigrationUI class. It checks whether there are any pending
    migrations before executing the decorated method, and raises a NothingToUpgradeError
    exception if there are none.

    Parameters
    ----------
    meth : Callable[MP, int]
        The method to be decorated. It should have a signature that matches the MP type hint.

    Returns
    -------
    Callable[MP, int]
        A wrapped method that checks if there are pending migrations before executing the
        migration method. If there are no applied migrations, returns TRANSACTION_NOT_APPLIED
        or raises NothingToUpgradeError if `raise_if_nothing_happens` configuration parameter
        is True.

    Raises
    ------
    NothingToUpgradeError
        If there are no pending migrations and raise_if_nothing_happens is True in the runtime
        configuration.
    """
    @functools.wraps(meth)
    def wrapper(self: MigrationUI, *args: MP.args, **kwargs: MP.kwargs) -> int:
        if not self.pending.has_migrations():
            if self.config.runtime.raise_if_nothing_happens:
                raise NothingToUpgradeError()

            return TRANSACTION_NOT_APPLIED

        return meth(self, *args, **kwargs)

    return wrapper


def requires_applied_migration(meth: typing.Callable[MP, int], /) -> typing.Callable[MP, int]:
    """A decorator that checks if there are applied migrations before executing
    a migration method. If there are no applied migrations and `raise_if_nothing_happens`
    configuration parameter is True, the decorator raises NothingToDowngradeError.

    Parameters
    ----------
    meth : Callable[MP, int]
        The migration method to be decorated.

    Returns
    -------
    Callable[MP, int]:
        A wrapped method that checks if there are applied migrations before executing the
        migration method. If there are no applied migrations, returns TRANSACTION_NOT_APPLIED
        or raises NothingToUpgradeError if `raise_if_nothing_happens` configuration parameter
        is True.

    Raises
    ------
    NothingToDowngradeError:
        If there are no applied migrations and `raise_if_nothing_happens` configuration parameter
        is True.
    """
    @functools.wraps(meth)
    def wrapper(self: MigrationUI, *args: MP.args, **kwargs: MP.kwargs) -> int:
        if not self.applied.has_migrations():
            if self.config.runtime.raise_if_nothing_happens:
                raise NothingToDowngradeError()

            return TRANSACTION_NOT_APPLIED

        return meth(self, *args, **kwargs)

    return wrapper


class ApplicationSession:
    """A class that represents migration application session.

    The `ApplicationSession` object holds a reference to a `MigrationUI` object which is used
    to manage database migrations.

    Parameters:
    -----------
    application : MigrationUI
        An instance of `MigrationUI` used for managing database migrations.
    """

    __slots__: typing.Sequence[str] = ("_application",)

    def __init__(self, application: MigrationUI, /) -> None:
        self._application = application

    def trigger_hooks(
        self,
        hooks: typing.Union[
            typing.List[PrioritizedMigrationHook],
            typing.List[MigrationHook],
        ],
        /,
    ) -> None:
        """Triggers hooks associated with a migration.

        Parameters
        ----------
        hooks : Union[List[PrioritizedMigrationHook], List[MigrationHook]]
            A list of hooks to be triggered.

        Notes
        -----
        The `trigger_hooks` method will receive a list of hooks and will trigger
        each one of them in the order specified by the hooks'  priority. If there
        is no prioritization, the hooks will be triggered in the order they were
        provided.
        """
        if hooks:
            if isinstance(hooks[0], PrioritizedMigrationHook):
                # TODO: do we really want to check if hooks are prioritized by the first element,
                #  at the developer agreement level?
                self._apply_prioritized_hooks(hooks)
                return

            self._apply_hooks(hooks)

    def _apply_prioritized_hooks(self, hooks: typing.List[PrioritizedMigrationHook], /) -> None:
        """Apply a list of prioritized migration hooks.

        Sorts the hooks by priority and applies them in priority order. If multiple hooks have
        the same priority, they will be executed in the order they were added.

        Parameters
        ----------
        hooks : List[PrioritizedMigrationHook
            A list of prioritized migration hooks to apply.
        """
        hooks.sort(key=operator.attrgetter("priority"))
        heapq.heapify(hooks)

        while hooks:
            proxy = heapq.heappop(hooks)
            proxy.item.apply(self._application)

            _LOGGER.info(
                "%s: (priority %s) hook checks completed successfully.",
                proxy.item.__class__.__name__,
                proxy.priority,
            )

    def _apply_hooks(self, hooks: typing.List[MigrationHook], /) -> None:
        """Apply a list of migration hooks to the application.

        Parameters
        ----------
        hooks : List[MigrationHook]
            The list of migration hooks to be applied.
        """
        for hook in hooks:
            hook.apply(self._application)

            _LOGGER.info(
                "%s: hook checks completed successfully.",
                hook.__class__.__name__,
            )

    @contextlib.contextmanager
    def start_transaction(self, transaction: TransactionT, /) -> typing.Iterator[TransactionT]:
        """Context manager for starting a transaction.

        Parameters
        ----------
        transaction : TransactionT
            A transaction object implementing `commit` and `rollback` methods.

        Yields
        ------
        TransactionT
            A context manager that yields the `transaction` argument.

        Raises
        ------
        MigrationTransactionFailedError
            If the transaction fails to commit and a rollback is needed.
        """
        _LOGGER.info(
            "Starting %s transaction...",
            transaction.__class__.__name__,
        )

        try:
            yield transaction
            transaction.commit()

            _LOGGER.info(
                "%s successfully commited.",
                transaction.__class__.__name__,
            )

        except BaseException as exc:
            _LOGGER.error(
                "%s transaction failed due to %s, rolling back...",
                transaction.__class__.__name__,
                exc.__class__.__name__,
            )
            transaction.rollback()
            raise MigrationTransactionFailedError() from exc


class MigrationUI(abc.ABC):
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

    @property
    @abc.abstractmethod
    def config(self) -> ApplicationConfig:
        """Return the configuration of the migration app.

        Returns
        -------
        ApplicationConfig
            The configuration of the migration app.
        """
        ...

    @property
    @abc.abstractmethod
    def session(self) -> ApplicationSession:
        """Return the session of the migration app.

        Returns
        -------
        ApplicationSession
            The session of the migration app.
        """
        ...

    @property
    @abc.abstractmethod
    def pending(self) -> MigrationQueue:
        """Return the pending migrations of the migration app.

        Returns
        -------
        MigrationQueue
            The pending migrations of the migration app.
        """
        ...

    @property
    @abc.abstractmethod
    def applied(self) -> MigrationQueue:
        """Return the applied migrations of the migration app.

        Returns
        -------
        MigrationQueue
            The applied migrations of the migration app.
        """
        ...

    @abc.abstractmethod
    def append_pending_migration(self, migration: Migration, /) -> None:
        """Append a migration to the list of pending migrations.

        Parameters
        ----------
        migration : Migration
            The migration to be added to the list of pending migrations.
        """
        ...

    @abc.abstractmethod
    def remove_pending_migration(self, migration_version: int, /) -> None:
        """Remove a pending migration with the given version number.

        Parameters
        ----------
        migration_version : int
            The version number of the migration to be removed.
        """
        ...

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
    def upgrade_while(self, predicate: typing.Callable[[Migration], bool], /) -> int:
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
    def downgrade_while(self, predicate: typing.Callable[[Migration], bool], /) -> int:
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

    @abc.abstractmethod
    def create_migration_file_template(
        self,
        migration_filename: str,
        migration_version: typing.Optional[int] = None,
    ) -> None:
        """Creates a new migration file template with the provided filename and version.

        Parameters
        ----------
        migration_filename : str
            The name of the migration file to be created.
        migration_version : int, optional
            The version number of the migration. If not provided, the next version number
            will be used based on the existing migrations. Defaults to None.

        Raises
        ------
        ValueError
            If a migration with the same version number already exists.
        """
        ...

    @abc.abstractmethod
    def get_migration_from_filename(self, migration_name: str) -> Migration:
        """Returns a Migration object corresponding to the migration with the given filename.

        Parameters
        ----------
        migration_name : str
            The name of the migration file to retrieve the Migration object for.

        Returns
        -------
        Migration
            A Migration object representing the migration with the given filename.
        """
        ...

    @abc.abstractmethod
    def get_migrations_from_directory(self) -> typing.Sequence[Migration]:
        """Returns a list of Migration objects representing all the migrations in the
        migrations directory.

        Returns
        -------
        Sequence[Migration]
            A list of Migration objects representing all the migrations in the
            migrations directory.

        Raises
        ------
        ValueError
            If the versioning start specified in the configuration is not found in the
            migrations directory.
        ImportError
            If `strict_naming` configuration parameter is False and migration file does
            not contain `version` variable.
        """
        ...

    @abc.abstractmethod
    def get_current_version(self) -> typing.Optional[int]:
        """Return the version of the latest applied migration, or None if no migrations
        have been applied yet.

        Returns
        -------
        Optional[int]
            The version of the latest applied migration, or None if no migrations have
            been applied yet.
        """
        ...


class BaseMigrationUI(MigrationUI):
    """A base class for implementing a migration UI.

    This class provides an implementation of the abstract `MigrationUI` class.
    It provides basic functionality for managing applied and pending migrations.

    Parameters
    ----------
    config : ApplicationConfig
        The configuration of the application.
    startup_hooks : Union[List[PrioritizedMigrationHook], List[MigrationHook]], optional
        The list of startup hooks to be triggered when the application starts.
    """

    __slots__: typing.Sequence[str] = (
        "_config",
        "_session",
        "_startup_hooks",
        "_applied_queue",
        "_pending_queue",
    )

    def __init__(
        self,
        config: ApplicationConfig,
        startup_hooks: typing.Optional[
            typing.Union[
                typing.List[PrioritizedMigrationHook],
                typing.List[MigrationHook],
            ]
        ] = None,
    ) -> None:
        logging.getLogger("mongorunway").setLevel(config.log.level)

        self._config = config
        self._startup_hooks = startup_hooks

        self._session = ApplicationSession(self)
        self._applied_queue = AppliedMigrationQueue(self)
        self._pending_queue = PendingMigrationQueue(self)

        if startup_hooks is not None:
            _LOGGER.info(
                "%s startup hooks found, running...",
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
        return self._config.name

    @property
    def config(self) -> ApplicationConfig:
        """Return the configuration of the migration app.

        Returns
        -------
        ApplicationConfig
            The configuration of the migration app.
        """
        return self._config

    @property
    def session(self) -> ApplicationSession:
        """Return the session of the migration app.

        Returns
        -------
        ApplicationSession
            The session of the migration app.
        """
        return self._session

    @property
    def pending(self) -> MigrationQueue:
        """Return the pending migrations of the migration app.

        Returns
        -------
        MigrationQueue
            The pending migrations of the migration app.
        """
        return self._pending_queue

    @property
    def applied(self) -> MigrationQueue:
        """Return the applied migrations of the migration app.

        Returns
        -------
        MigrationQueue
            The applied migrations of the migration app.
        """
        return self._applied_queue

    def append_pending_migration(self, migration: Migration, /) -> None:
        """Append a migration to the list of pending migrations.

        Parameters
        ----------
        migration : Migration
            The migration to be added to the list of pending migrations.

        Notes
        -----
        If the given migration is already present in either the pending or applied
        migrations list, it will not be added again.
        """
        if not self.pending.has_migration(migration) and not self.applied.has_migration(migration):
            self.pending.append_migration(migration)

    def remove_pending_migration(self, migration_version: int, /) -> None:
        """Remove a pending migration with the given version number.

        Parameters
        ----------
        migration_version : int
            The version number of the migration to be removed.

        Notes
        -----
        This method removes a pending migration with the given version number from
        the list of pending migrations. If no migration with the given version number
        is found in the list, this method has no effect.
        """
        if self.pending.has_migration_with_version(migration_version):
            self.pending.remove_migration(migration_version)

    @requires_pending_migration
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
        migration = self.pending.pop_waiting_migration()

        _LOGGER.info(
            "%s: upgrading waiting migration (#%s -> #%s)...",
            self.name,
            get_previous_version(migration),
            migration.version,
        )

        with self._session.start_transaction(UpgradeTransaction(self)) as transaction:
            transaction.apply_migration(migration)

            _LOGGER.info(
                "%s: Successfully upgraded to (#%s).",
                self.name,
                migration.version,
            )
            return TRANSACTION_SUCCESS

    @requires_applied_migration
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
        migration = self.applied.pop_waiting_migration()

        _LOGGER.info(
            "%s: downgrading waiting migration (#%s -> #%s)...",
            self.name,
            migration.version,
            get_previous_version(migration),
        )

        with self._session.start_transaction(DowngradeTransaction(self)) as transaction:
            transaction.apply_migration(migration)

            _LOGGER.info(
                "%s: successfully downgraded to (#%s).",
                self.name,
                migration.version,
            )
            return TRANSACTION_SUCCESS

    @requires_pending_migration
    def upgrade_while(self, predicate: typing.Callable[[Migration], bool], /) -> int:
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

        while self.pending.has_migrations():
            migration = self.pending.pop_waiting_migration()

            if not predicate(migration):
                self.pending.append_migration(migration)
                break

            _LOGGER.info(
                "%s: upgrading waiting migration (#%s -> #%s)...",
                self.name,
                get_previous_version(migration),
                migration.version,
            )

            with self._session.start_transaction(UpgradeTransaction(self)) as transaction:
                transaction.apply_migration(migration)

            _LOGGER.info(
                "%s: Successfully upgraded to (#%s).",
                self.name,
                migration.version,
            )
            upgraded += 1

        return upgraded

    @requires_applied_migration
    def downgrade_while(self, predicate: typing.Callable[[Migration], bool], /) -> int:
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

        while self.applied.has_migrations():
            migration = self.applied.pop_waiting_migration()

            _LOGGER.info(
                "%s: downgrading waiting migration (#%s -> #%s)...",
                self.name,
                migration.version,
                get_previous_version(migration),
            )

            if not predicate(migration):
                self.applied.append_migration(migration)
                break

            with self._session.start_transaction(DowngradeTransaction(self)) as transaction:
                transaction.apply_migration(migration)

            _LOGGER.info(
                "%s: successfully downgraded to (#%s).",
                self.name,
                migration.version,
            )
            downgraded += 1

        return downgraded

    @requires_applied_migration
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

        if not self.applied.has_migration_with_version(migration_version):
            raise ValueError(f"Migration version {migration_version} not found.")

        return self.downgrade_while(lambda m: m.version > migration_version)

    @requires_pending_migration
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
        if not self.pending.has_migration_with_version(migration_version):
            raise ValueError(f"Migration version {migration_version} not found.")

        return self.upgrade_while(lambda m: m.version <= migration_version)

    @requires_applied_migration
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

    @requires_pending_migration
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

    def create_migration_file_template(
        self,
        migration_filename: str,
        migration_version: typing.Optional[int] = None,
    ) -> None:
        """Creates a new migration file template with the provided filename and version.

        Parameters
        ----------
        migration_filename : str
            The name of the migration file to be created.
        migration_version : int, optional
            The version number of the migration. If not provided, the next version number
            will be used based on the existing migrations. Defaults to None.

        Raises
        ------
        ValueError
            If a migration with the same version number already exists.
        """
        if migration_version is None:
            migration_version = len(self.get_migrations_from_directory()) + 1

        if self.pending.has_migration_with_version(
            migration_version
        ) or self.applied.has_migration_with_version(migration_version):
            raise ValueError(f"Migration with version {migration_version} already exist.")

        if self.config.runtime.strict_naming:
            migration_filename = self.config.runtime.filename_strategy.transform_migration_filename(
                migration_filename,
                migration_version,
            )

            if not migration_filename.endswith(".py"):
                migration_filename += ".py"

        with open(os.path.join(self.config.migration_scripts_dir, migration_filename), "w") as f:
            f.write(
                migration_file_template.substitute(
                    upgrade_commands=[],
                    downgrade_commands=[],
                    version=migration_version,
                )
            )

    def get_migration_from_filename(self, migration_name: str) -> Migration:
        """Returns a Migration object corresponding to the migration with the given filename.

        Parameters
        ----------
        migration_name : str
            The name of the migration file to retrieve the Migration object for.

        Returns
        -------
        Migration
            A Migration object representing the migration with the given filename.
        """
        module = util.get_module(self.config.migration_scripts_dir, migration_name)
        migration_module = MigrationModule(module)

        migration = BaseMigration(
            name=migration_module.get_name(),
            version=module.version,
            description=migration_module.description,
            checksum=calculate_migration_checksum(migration_module),
            downgrade_commands=migration_module.get_downgrade_commands(),
            upgrade_commands=migration_module.get_upgrade_commands(),
        )

        return migration

    def get_migrations_from_directory(self) -> typing.Sequence[Migration]:
        """Returns a list of Migration objects representing all the migrations in the
        migrations directory.

        Returns
        -------
        Sequence[Migration]
            A list of Migration objects representing all the migrations in the
            migrations directory.

        Raises
        ------
        ValueError
            If the versioning start specified in the configuration is not found in the
            migrations directory.
        ImportError
            If `strict_naming` configuration parameter is False and migration file does
            not contain `version` variable.
        """
        directory = self.config.migration_scripts_dir
        filename_strategy = self.config.runtime.filename_strategy

        if self.config.runtime.strict_naming:
            # All migrations are in the correct order by name.
            migrations = [
                self.get_migration_from_filename(
                    filename_strategy.transform_migration_filename(migration_name, position),
                )
                for position, migration_name in enumerate(
                    sorted(os.listdir(directory)), self.config.invariants.versioning_starts_from,
                )
                if util.is_valid_migration_filename(directory, migration_name)
            ]
        else:
            migrations = {}
            for migration_name in sorted(os.listdir(directory)):
                if not util.is_valid_migration_filename(directory, migration_name):
                    continue

                module = util.get_module(directory, migration_name)
                try:
                    migration_version = module.version
                except AttributeError:
                    raise ImportError(
                        f"Migration {migration_name} in non-strict mode must have 'version' variable."
                    )

                migrations[migration_version] = self.get_migration_from_filename(
                    migration_name,
                )

            if (start := self.config.invariants.versioning_starts_from) not in migrations:
                # ...
                raise ValueError(f"Versioning starts from {start}.")

            migrations = [migrations[key] for key in sorted(migrations.keys())]

        return migrations

    def get_current_version(self) -> typing.Optional[int]:
        """Return the version of the latest applied migration, or None if no migrations
        have been applied yet.

        Returns
        -------
        Optional[int]
            The version of the latest applied migration, or None if no migrations have
            been applied yet.
        """
        if (target := self.applied.acquire_latest_migration()) is not None:
            target = target.version

        return target
