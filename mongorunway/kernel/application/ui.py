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
    @functools.wraps(meth)
    def wrapper(self: MigrationUI, *args: MP.args, **kwargs: MP.kwargs) -> int:
        if not self.pending.has_migrations():
            if self.config.runtime.raise_if_nothing_happens:
                raise NothingToUpgradeError()
            return TRANSACTION_NOT_APPLIED
        return meth(self, *args, **kwargs)

    return wrapper


def requires_applied_migration(meth: typing.Callable[MP, int], /) -> typing.Callable[MP, int]:
    @functools.wraps(meth)
    def wrapper(self: MigrationUI, *args: MP.args, **kwargs: MP.kwargs) -> int:
        if not self.applied.has_migrations():
            if self.config.runtime.raise_if_nothing_happens:
                raise NothingToDowngradeError()
            return TRANSACTION_NOT_APPLIED
        return meth(self, *args, **kwargs)

    return wrapper


class ApplicationSession:
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
        if hooks:
            if isinstance(hooks[0], PrioritizedMigrationHook):
                # TODO: do we really want to check if hooks are prioritized by the first element,
                #  at the developer agreement level?
                self._apply_prioritized_hooks(hooks)
                return

            self._apply_hooks(hooks)

    def _apply_prioritized_hooks(self, hooks: typing.List[PrioritizedMigrationHook], /) -> None:
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
        for hook in hooks:
            hook.apply(self._application)

            _LOGGER.info(
                "%s: hook checks completed successfully.",
                hook.__class__.__name__,
            )

    @contextlib.contextmanager
    def start_transaction(self, transaction: TransactionT, /) -> typing.Iterator[TransactionT]:
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
    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def config(self) -> ApplicationConfig:
        ...

    @property
    @abc.abstractmethod
    def session(self) -> ApplicationSession:
        ...

    @property
    @abc.abstractmethod
    def pending(self) -> MigrationQueue:
        ...

    @property
    @abc.abstractmethod
    def applied(self) -> MigrationQueue:
        ...

    @abc.abstractmethod
    def append_pending_migration(self, migration: Migration, /) -> None:
        ...

    @abc.abstractmethod
    def remove_pending_migration(self, migration_version: int, /) -> None:
        ...

    @abc.abstractmethod
    def upgrade_once(self) -> int:
        ...

    @abc.abstractmethod
    def downgrade_once(self) -> int:
        ...

    @abc.abstractmethod
    def upgrade_while(self, predicate: typing.Callable[[Migration], bool], /) -> int:
        ...

    @abc.abstractmethod
    def downgrade_while(self, predicate: typing.Callable[[Migration], bool], /) -> int:
        ...

    @abc.abstractmethod
    def downgrade_to(self, migration_version: int, /) -> int:
        ...

    @abc.abstractmethod
    def upgrade_to(self, migration_version: int, /) -> int:
        ...

    @abc.abstractmethod
    def downgrade_all(self) -> int:
        ...

    @abc.abstractmethod
    def upgrade_all(self) -> int:
        ...

    @abc.abstractmethod
    def create_migration_file_template(
        self,
        migration_filename: str,
        migration_version: typing.Optional[int] = None,
    ) -> None:
        ...

    @abc.abstractmethod
    def get_migration_from_filename(self, migration_name: str) -> Migration:
        ...

    @abc.abstractmethod
    def get_migrations_from_directory(self) -> typing.Sequence[Migration]:
        ...

    @abc.abstractmethod
    def get_current_version(self) -> typing.Optional[int]:
        ...


class BaseMigrationUI(MigrationUI):
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
        return self._config.name

    @property
    def config(self) -> ApplicationConfig:
        return self._config

    @property
    def session(self) -> ApplicationSession:
        return self._session

    @property
    def pending(self) -> MigrationQueue:
        return self._pending_queue

    @property
    def applied(self) -> MigrationQueue:
        return self._applied_queue

    def append_pending_migration(self, migration: Migration, /) -> None:
        if not self.pending.has_migration(migration) and not self.applied.has_migration(migration):
            self.pending.append_migration(migration)

    def remove_pending_migration(self, migration_version: int, /) -> None:
        if self.pending.has_migration_with_version(migration_version):
            self.pending.remove_migration(migration_version)

    @requires_pending_migration
    def upgrade_once(self) -> int:
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
                migration,
            )
            return TRANSACTION_SUCCESS

    @requires_pending_migration
    def upgrade_while(self, predicate: typing.Callable[[Migration], bool], /) -> int:
        upgraded = 0

        while self.pending.has_migrations():
            migration = self.pending.pop_waiting_migration()

            if not predicate(migration):
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

    def downgrade_to(self, migration_version: int, /) -> int:
        if not migration_version:
            return self.downgrade_all()

        if not self.applied.has_migration_with_version(migration_version):
            raise ValueError(f"Migration version {migration_version} not found.")

        return self.downgrade_while(lambda m: m.version > migration_version)

    def upgrade_to(self, migration_version: int, /) -> int:
        if not self.pending.has_migration_with_version(migration_version):
            raise ValueError(f"Migration version {migration_version} not found.")

        return self.upgrade_while(lambda m: m.version <= migration_version)

    def downgrade_all(self) -> int:
        return self.downgrade_while(lambda _: True)

    def upgrade_all(self) -> int:
        return self.upgrade_while(lambda _: True)

    def create_migration_file_template(
        self,
        migration_filename: str,
        migration_version: typing.Optional[int] = None,
    ) -> None:
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
        if (target := self.applied.acquire_latest_migration()) is not None:
            target = target.version

        return target
