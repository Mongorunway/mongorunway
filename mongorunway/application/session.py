from __future__ import annotations

import abc
import datetime
import heapq
import logging
import operator
import typing
import uuid

import bson

from mongorunway.application import transactions
from mongorunway.application.ports import hook as hook_port
from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_auditlog_entry as domain_auditlog_entry
from mongorunway.domain import migration_exception as domain_exception

if typing.TYPE_CHECKING:
    from mongorunway import mongo
    from mongorunway.application import applications
    from mongorunway.application import config
    from mongorunway.application.ports import auditlog_journal as auditlog_journal_port
    from mongorunway.application.ports import repository as repository_port
    from mongorunway.domain import migration_business_rule as domain_rule

TransactionT = typing.TypeVar("TransactionT", bound=transactions.MigrationTransaction)

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("mongorunway.session")


class LoggedTransactionContext(typing.Generic[TransactionT]):
    def __init__(
        self,
        migration_session: MigrationSession,
        transaction_type: typing.Type[TransactionT],
    ) -> None:
        self._transaction = transaction_type.create(migration_session)
        self._migration_session = migration_session

    def __enter__(self) -> TransactionT:
        return self._transaction

    def __exit__(self, *args: typing.Any) -> None:
        if self._migration_session.is_auditlog_enabled():
            entry = self._build_auditlog_entry()

            if self._transaction.is_failed():
                assert self._transaction.exc_val is not None  # For type checkers only
                entry.with_error(self._transaction.exc_val)

                self._migration_session.log_audit_entry(entry)

    def _build_auditlog_entry(self) -> domain_auditlog_entry.MigrationAuditlogEntry:
        entry = domain_auditlog_entry.MigrationAuditlogEntry(
            session_id=self._migration_session.session_id,
            transaction_name=type(self._transaction).__name__,
            migration=domain_migration.MigrationReadModel.from_migration(
                self._transaction.ensure_migration(),
            ),
        )

        if self._migration_session.has_unique_timezone():
            entry.with_timezone(self._migration_session.session_timezone)

        return entry


class MigrationSession(abc.ABC):
    __slots__ = ()

    @property
    @abc.abstractmethod
    def session_config(self) -> config.Config:
        ...

    @property
    @abc.abstractmethod
    def session_id(self) -> bson.binary.Binary:
        ...

    @property
    @abc.abstractmethod
    def session_timezone(self) -> str:
        ...

    @abc.abstractmethod
    def is_logged(self) -> bool:
        ...

    @abc.abstractmethod
    def is_auditlog_enabled(self) -> bool:
        ...

    @abc.abstractmethod
    def has_unique_timezone(self) -> bool:
        ...

    @abc.abstractmethod
    def trigger_hooks(self, hooks: hook_port.MixedHookList, /) -> None:
        ...

    @abc.abstractmethod
    def history(
        self,
        start: typing.Optional[datetime.datetime] = None,
        end: typing.Optional[datetime.datetime] = None,
        limit: typing.Optional[int] = None,
        ascending_date: bool = True,
    ) -> typing.Iterator[domain_auditlog_entry.MigrationAuditlogEntry]:
        ...

    @abc.abstractmethod
    def validate_migration_process(
        self,
        migration_process: domain_migration.MigrationProcess,
        /,
        client: mongo.Client,
    ) -> None:
        ...

    @abc.abstractmethod
    def has_migration(self, item: typing.Any, /) -> bool:
        ...

    @abc.abstractmethod
    def has_migration_with_version(self, migration_version: int, /) -> bool:
        ...

    @abc.abstractmethod
    def has_migrations(self) -> bool:
        ...

    @abc.abstractmethod
    def get_migration_model_by_version(
        self,
        migration_version: int,
    ) -> typing.Optional[domain_migration.MigrationReadModel]:
        ...

    @abc.abstractmethod
    def get_migration_model_by_flag(
        self,
        *,
        is_applied: bool,
    ) -> typing.Optional[domain_migration.MigrationReadModel]:
        ...

    @abc.abstractmethod
    def get_all_migration_models(
        self,
        *,
        ascending_id: bool = True,
    ) -> typing.Sequence[domain_migration.MigrationReadModel]:
        ...

    @abc.abstractmethod
    def get_migration_models_by_flag(
        self, *, is_applied: bool
    ) -> typing.Sequence[domain_migration.MigrationReadModel]:
        ...

    @abc.abstractmethod
    def append_pending_migration(self, migration: domain_migration.Migration, /) -> None:
        ...

    @abc.abstractmethod
    def remove_pending_migration(self, migration_version: int, /) -> None:
        ...

    @abc.abstractmethod
    def get_current_version(self) -> typing.Optional[int]:
        ...

    @abc.abstractmethod
    def set_applied_flag(self, migration: domain_migration.Migration, is_applied: bool) -> None:
        ...

    @abc.abstractmethod
    def log_audit_entry(
        self, migration_auditlog_entry: domain_auditlog_entry.MigrationAuditlogEntry, /
    ) -> None:
        ...

    @abc.abstractmethod
    def begin_transaction(
        self, transaction_type: typing.Type[TransactionT], /
    ) -> LoggedTransactionContext[TransactionT]:
        ...


class MigrationSessionImpl(MigrationSession):
    def __init__(
        self,
        app: applications.MigrationApp,
        configuration: config.Config,
        repository: repository_port.MigrationRepository,
        auditlog_journal: typing.Optional[auditlog_journal_port.AuditlogJournal],
    ) -> None:
        self._config = configuration
        self._repository = repository
        self._application = app
        self._auditlog_journal = auditlog_journal

    @property
    def session_id(self) -> bson.binary.Binary:
        return bson.binary.Binary(uuid.uuid4().bytes, bson.UUID_SUBTYPE)  # like in pymongo session

    @property
    def session_timezone(self) -> str:
        return self.session_config.application.app_timezone

    @property
    def session_config(self) -> config.Config:
        return self._config

    def is_logged(self) -> bool:
        return self.session_config.application.is_logged()

    def has_unique_timezone(self) -> bool:
        return self.session_config.application.has_unique_timezone()

    def is_auditlog_enabled(self) -> bool:
        return self.session_config.application.is_auditlog_enabled()

    def validate_migration_process(
        self,
        migration_process: domain_migration.MigrationProcess,
        /,
        client: mongo.Client,
    ) -> None:
        if migration_process.has_rules():
            _LOGGER.info(
                "Starting validation of migration process with version %s...",
                migration_process.migration_version,
            )

            def _validate_deps_recursive(
                depends_on: typing.Sequence[domain_rule.MigrationBusinessRule],
            ) -> None:
                for r in depends_on:
                    if r.check_is_broken(client):
                        _LOGGER.error("%s rule failed, raising...", r.name)
                        raise domain_exception.MigrationBusinessRuleBrokenError(r)

                    _LOGGER.info("%s rule successfully passed.", r.name)

                    if r.is_independent():
                        continue

                    _validate_deps_recursive(r.depends_on)

            for rule in migration_process.rules:
                _validate_deps_recursive(rule.depends_on)

                if rule.check_is_broken(client):
                    _LOGGER.error("%s rule failed, raising...", rule.name)
                    raise domain_exception.MigrationBusinessRuleBrokenError(rule)

                _LOGGER.info("%s rule successfully passed.", rule.name)

    def has_migration(self, item: typing.Any, /) -> bool:
        return self._repository.has_migration(item)

    def has_migration_with_version(self, migration_version: int, /) -> bool:
        if not isinstance(migration_version, int):
            raise TypeError(f"Migration version must be instance of {int!r}.")

        return self._repository.has_migration_with_version(migration_version)

    def has_migrations(self) -> bool:
        return self._repository.has_migrations()

    def get_migration_model_by_version(
        self, migration_version: int
    ) -> typing.Optional[domain_migration.MigrationReadModel]:
        if not isinstance(migration_version, int):
            raise TypeError(f"Migration version must be instance of {int!r}.")

        return self._repository.acquire_migration_model_by_version(migration_version)

    def get_migration_model_by_flag(
        self,
        *,
        is_applied: bool,
    ) -> typing.Optional[domain_migration.MigrationReadModel]:
        return self._repository.acquire_migration_model_by_flag(is_applied)

    def get_all_migration_models(
        self,
        *,
        ascending_id: bool = True,
    ) -> typing.MutableSequence[domain_migration.MigrationReadModel]:
        return self._repository.acquire_all_migration_models(ascending_id=ascending_id)

    def get_migration_models_by_flag(
        self,
        *,
        is_applied: bool,
    ) -> typing.MutableSequence[domain_migration.MigrationReadModel]:
        return list(self._repository.acquire_migration_models_by_flag(is_applied=is_applied))

    def get_current_version(self) -> typing.Optional[int]:
        if (
            target := self._repository.acquire_migration_model_by_flag(is_applied=True)
        ) is not None:
            return target.version

        return target

    def append_pending_migration(self, migration: domain_migration.Migration, /) -> None:
        if not isinstance(migration, domain_migration.Migration):
            raise TypeError(f"Migration must be instance of {domain_migration.Migration!r}.")

        if migration.is_applied:
            raise ValueError(f"Migration with version {migration.version} is already applied.")

        self._repository.append_migration(migration)

    def remove_pending_migration(self, migration_version: int, /) -> None:
        if not isinstance(migration_version, int):
            raise TypeError(f"Migration version must be instance of {int!r}.")

        model = self._repository.acquire_migration_model_by_version(migration_version)
        if model is None:
            raise ValueError(f"Pending migration with version {migration_version} does not exist.")

        self._repository.remove_migration(migration_version)

    def set_applied_flag(self, migration: domain_migration.Migration, is_applied: bool) -> None:
        if not isinstance(migration, domain_migration.Migration):
            raise TypeError(f"Migration must be instance of {domain_migration.Migration!r}.")

        self._repository.set_applied_flag(migration, is_applied)

    def log_audit_entry(self, entry: domain_auditlog_entry.MigrationAuditlogEntry) -> None:
        if not isinstance(entry, domain_auditlog_entry.MigrationAuditlogEntry):
            raise TypeError(
                f"Migration auditlog entry must be instance of "
                f"{domain_auditlog_entry.MigrationAuditlogEntry!r}."
            )

        if not self.is_logged():
            raise ValueError("Audit log is not enabled in this session.")

        assert self._auditlog_journal is not None  # For type checkers only
        self._auditlog_journal.append_entries([entry])

    def history(
        self,
        start: typing.Optional[datetime.datetime] = None,
        end: typing.Optional[datetime.datetime] = None,
        limit: typing.Optional[int] = None,
        ascending_date: bool = True,
    ) -> typing.Iterator[domain_auditlog_entry.MigrationAuditlogEntry]:
        if not self.is_logged():
            raise ValueError("Audit log is not enabled in this session.")

        assert self._auditlog_journal is not None  # For type checkers only
        yield from self._auditlog_journal.history(
            start=start,
            end=end,
            limit=limit,
            ascending_date=ascending_date,
        )

    def begin_transaction(
        self, transaction_type: typing.Type[TransactionT], /
    ) -> LoggedTransactionContext[TransactionT]:
        return LoggedTransactionContext(self, transaction_type)

    def trigger_hooks(self, hooks: hook_port.MixedHookList, /) -> None:
        if hooks:
            prioritized_hooks = []
            normal_hooks = []

            for hook in hooks:
                if isinstance(hook, hook_port.PrioritizedMigrationHook):
                    prioritized_hooks.append(hook)
                else:
                    assert isinstance(hook, hook_port.MigrationHook)  # For type checkers only
                    normal_hooks.append(hook)

            self._apply_prioritized_hooks(prioritized_hooks)
            self._apply_hooks(normal_hooks)

    def _apply_prioritized_hooks(
        self, hooks: typing.List[hook_port.PrioritizedMigrationHook], /
    ) -> None:
        hooks.sort(key=operator.attrgetter("priority"))
        heapq.heapify(hooks)

        while hooks:
            proxy = heapq.heappop(hooks)
            proxy.item.apply(self._application)

            _LOGGER.info(
                "%s: (priority %s) hook execution completed successfully.",
                proxy.item.__class__.__name__,
                proxy.priority,
            )

    def _apply_hooks(self, hooks: typing.List[hook_port.MigrationHook], /) -> None:
        for hook in hooks:
            hook.apply(self._application)

            _LOGGER.info(
                "%s hook execution completed successfully.",
                hook.__class__.__name__,
            )
