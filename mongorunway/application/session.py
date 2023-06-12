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
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "MigrationSessionImpl",
    "MigrationSession",
    "MongoSessionContextT",
    "MongoSessionContext",
    "TransactionT",
    "TransactionContext",
    "requires_auditlog",
)

import abc
import contextlib
import datetime
import functools
import logging
import typing
import uuid

import bson
import typing_extensions

from mongorunway import mongo
from mongorunway import util
from mongorunway.application import transactions
from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_auditlog_entry as domain_auditlog_entry

if typing.TYPE_CHECKING:
    from mongorunway.application import applications
    from mongorunway.application import config
    from mongorunway.application.ports import filename_strategy as filename_strategy_port
    from mongorunway.domain import migration_event as domain_event

try:
    _P = typing.ParamSpec("_P")
except AttributeError:
    _P = typing_extensions.ParamSpec("_P")

_T = typing.TypeVar("_T")

TransactionT = typing.TypeVar("TransactionT", bound=transactions.MigrationTransaction)
MongoSessionContextT = typing.TypeVar("MongoSessionContextT", bound="MongoSessionContext")

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("mongorunway.session")


def requires_auditlog(meth: typing.Callable[_P, _T]) -> typing.Callable[_P, _T]:
    @functools.wraps(meth)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _T:
        self: "MigrationSession" = typing.cast("MigrationSession", args[0])
        if not self.uses_auditlog:
            raise ValueError("Auditlog is not enabled on this session.")

        return meth(*args, **kwargs)

    return typing.cast(typing.Callable[_P, _T], wrapper)


class TransactionContext(typing.Generic[TransactionT]):
    def __init__(
        self,
        migration_session: MigrationSession,
        transaction_type: typing.Type[TransactionT],
        migration: domain_migration.Migration,
    ) -> None:
        self._transaction = transaction_type.create(migration_session, migration)
        self._migration = migration
        self._migration_session = migration_session

    def __enter__(self) -> TransactionT:
        return self._transaction

    def __exit__(self, *args: typing.Any) -> None:
        if self._migration_session.uses_auditlog:
            entry = self._build_auditlog_entry()

            if self._transaction.is_failed():
                assert self._transaction.exc_val is not None  # For type checkers only
                entry.with_error(self._transaction.exc_val)

            self._migration_session.log_audit_entry(entry)

    def _build_auditlog_entry(self) -> domain_auditlog_entry.MigrationAuditlogEntry:
        entry = domain_auditlog_entry.MigrationAuditlogEntry(
            date_fmt=self._migration_session.session_date_format,
            session_id=self._migration_session.session_id,
            transaction_name=type(self._transaction).__name__,
            migration_read_model=domain_migration.MigrationReadModel.from_migration(
                self._migration,
            ),
        )

        if self._migration_session.uses_unique_timezone:
            entry.with_timezone(self._migration_session.session_timezone)

        return entry


class MongoSessionContext:
    # incapsulate
    def __init__(self, session: mongo.ClientSession) -> None:
        self.__session = session

    def __enter__(self: MongoSessionContextT) -> MongoSessionContextT:
        return self

    def __exit__(self, *args: typing.Any) -> None:
        self.__session.end_session()

    @property
    def mongodb_session_id(self) -> bson.binary.Binary:
        return typing.cast(
            bson.binary.Binary,
            self.__session.session_id["id"],
        )

    @property
    def has_ended(self) -> bool:
        return self.__session.has_ended

    def start_transaction(
        self,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> contextlib.AbstractContextManager[typing.Any]:
        return self.__session.start_transaction(*args, **kwargs)

    def commit_transaction(self) -> None:
        return self.__session.commit_transaction()

    def abort_transaction(self) -> None:
        return self.__session.abort_transaction()


class MigrationSession(abc.ABC):
    __slots__ = ()

    @property
    @abc.abstractmethod
    def session_id(self) -> bson.binary.Binary:
        ...

    @property
    @abc.abstractmethod
    def session_timezone(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def session_date_format(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def session_client(self) -> mongo.Client:
        ...

    @property
    @abc.abstractmethod
    def session_database(self) -> mongo.Database:
        ...

    @property
    @abc.abstractmethod
    def session_name(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def session_subscribed_events(
        self,
    ) -> typing.Mapping[
        typing.Type[domain_event.MigrationEvent],
        typing.Sequence[domain_event.EventHandlerProxyOr[domain_event.EventHandler]],
    ]:
        ...

    @property
    @abc.abstractmethod
    def session_auditlog_limit(self) -> typing.Optional[int]:
        ...

    @property
    @abc.abstractmethod
    def session_config_dir(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def session_scripts_dir(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def session_file_naming_strategy(self) -> filename_strategy_port.FilenameStrategy:
        ...

    @property
    @abc.abstractmethod
    def uses_strict_file_naming(self) -> bool:
        ...

    @property
    @abc.abstractmethod
    def uses_schema_validation(self) -> bool:
        ...

    @property
    @abc.abstractmethod
    def uses_indexing(self) -> bool:
        ...

    @property
    @abc.abstractmethod
    def uses_logging(self) -> bool:
        ...

    @property
    @abc.abstractmethod
    def uses_unique_timezone(self) -> bool:
        ...

    @property
    @abc.abstractmethod
    def uses_auditlog(self) -> bool:
        ...

    @property
    @abc.abstractmethod
    def raises_on_transaction_failure(self) -> bool:
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
    ) -> typing.MutableSequence[domain_migration.MigrationReadModel]:
        ...

    @abc.abstractmethod
    def get_migration_models_by_flag(
        self, *, is_applied: bool
    ) -> typing.MutableSequence[domain_migration.MigrationReadModel]:
        ...

    @abc.abstractmethod
    def append_migration(self, migration: domain_migration.Migration, /) -> None:
        ...

    @abc.abstractmethod
    def remove_migration(self, migration_version: int, /) -> None:
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
    def begin_mongo_session(self) -> MongoSessionContext:
        ...

    @abc.abstractmethod
    def begin_transaction(
        self,
        transaction_type: typing.Type[TransactionT],
        migration: domain_migration.Migration,
    ) -> TransactionContext[TransactionT]:
        ...


class MigrationSessionImpl(MigrationSession):
    def __init__(
        self,
        app: applications.MigrationApp,
        configuration: config.Config,
    ) -> None:
        self._config = configuration
        self._application = app

        self._repository = configuration.application.app_repository
        self._auditlog_journal = configuration.application.app_auditlog_journal

    @property
    def session_id(self) -> bson.binary.Binary:
        return bson.binary.Binary(uuid.uuid4().bytes, bson.UUID_SUBTYPE)  # like in pymongo session

    @property
    def session_timezone(self) -> str:
        return self._config.application.app_timezone

    @property
    def session_date_format(self) -> str:
        return self._config.application.app_date_format

    @property
    def session_client(self) -> mongo.Client:
        return self._config.application.app_client

    @property
    def session_database(self) -> mongo.Database:
        return self._config.application.app_database

    @property
    def session_name(self) -> str:
        return self._config.application.app_name

    @property
    def session_subscribed_events(
        self,
    ) -> typing.Mapping[
        typing.Type[domain_event.MigrationEvent],
        typing.Sequence[domain_event.EventHandlerProxyOr[domain_event.EventHandler]],
    ]:
        return self._config.application.app_events

    @property
    def session_auditlog_limit(self) -> typing.Optional[int]:
        return self._config.application.app_auditlog_limit

    @property
    def session_config_dir(self) -> str:
        return self._config.filesystem.config_dir

    @property
    def session_scripts_dir(self) -> str:
        return self._config.filesystem.scripts_dir

    @property
    def session_file_naming_strategy(self) -> filename_strategy_port.FilenameStrategy:
        return self._config.filesystem.filename_strategy

    @property
    def uses_strict_file_naming(self) -> bool:
        return self._config.filesystem.use_filename_strategy

    @property
    def uses_schema_validation(self) -> bool:
        return self._config.application.use_schema_validation

    @property
    def uses_indexing(self) -> bool:
        return self._config.application.use_indexing

    @property
    def uses_logging(self) -> bool:
        return self._config.application.is_logged

    @property
    def uses_unique_timezone(self) -> bool:
        return self._config.application.has_unique_timezone

    @property
    def uses_auditlog(self) -> bool:
        return self._config.application.is_auditlog_enabled

    @property
    def raises_on_transaction_failure(self) -> bool:
        return self._config.application.raise_on_transaction_failure

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
        return list(self._repository.acquire_all_migration_models(ascending_id=ascending_id))

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
            return typing.cast(
                typing.Optional[int],
                target.version,
            )

        return target

    def append_migration(self, migration: domain_migration.Migration, /) -> None:
        if not isinstance(migration, domain_migration.Migration):
            raise TypeError(f"Migration must be instance of {domain_migration.Migration!r}.")

        self._repository.append_migration(migration)

    def remove_migration(self, migration_version: int, /) -> None:
        if not isinstance(migration_version, int):
            raise TypeError(f"Migration version must be instance of {int!r}.")

        model = self._repository.acquire_migration_model_by_version(migration_version)
        if model is None:
            raise ValueError(f"Migration with version {migration_version} does not exist.")

        self._repository.remove_migration(migration_version)

    def set_applied_flag(self, migration: domain_migration.Migration, is_applied: bool) -> None:
        if not isinstance(migration, domain_migration.Migration):
            raise TypeError(f"Migration must be instance of {domain_migration.Migration!r}.")

        self._repository.set_applied_flag(migration, is_applied)

    @requires_auditlog
    def log_audit_entry(self, entry: domain_auditlog_entry.MigrationAuditlogEntry) -> None:
        if not isinstance(entry, domain_auditlog_entry.MigrationAuditlogEntry):
            raise TypeError(
                f"Migration auditlog entry must be instance of "
                f"{domain_auditlog_entry.MigrationAuditlogEntry!r}."
            )

        assert self._auditlog_journal is not None  # For type checkers only
        self._auditlog_journal.append_entries([entry])

    @requires_auditlog
    def history(
        self,
        start: typing.Optional[datetime.datetime] = None,
        end: typing.Optional[datetime.datetime] = None,
        limit: typing.Optional[int] = None,
        ascending_date: bool = True,
    ) -> typing.Iterator[domain_auditlog_entry.MigrationAuditlogEntry]:
        assert self._auditlog_journal is not None  # For type checkers only
        yield from self._auditlog_journal.history(
            start=start,
            end=end,
            limit=limit,
            ascending_date=ascending_date,
        )

    def begin_mongo_session(self) -> MongoSessionContext:
        ctx = MongoSessionContext(self.session_client.start_session())
        _LOGGER.info(
            "Mongorunway MongoDB context successfully initialized " "with MongoDB session id (%s)",
            util.hexlify(ctx.mongodb_session_id),
        )
        return ctx

    def begin_transaction(
        self,
        transaction_type: typing.Type[TransactionT],
        migration: domain_migration.Migration,
    ) -> TransactionContext[TransactionT]:
        ctx = TransactionContext(self, transaction_type, migration)
        _LOGGER.info(
            "Mongorunway transaction context successfully initialized "
            "with Mongorunway session id (%s)",
            util.hexlify(self.session_id),
        )
        return ctx
