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
import logging
import typing

from mongorunway import util
from mongorunway.application import session
from mongorunway.application.services import validation_service
from mongorunway.domain import migration_context as domain_context

if typing.TYPE_CHECKING:
    from mongorunway.domain import migration as domain_migration

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("mongorunway.transactions")
_SelfT = typing.TypeVar("_SelfT", bound="MigrationTransaction")

TransactionCode: typing.TypeAlias = int

TRANSACTION_SUCCESS: typing.Final[TransactionCode] = 1

TRANSACTION_NOT_APPLIED: typing.Final[TransactionCode] = 0


class MigrationTransaction(abc.ABC):
    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def exc_val(self) -> typing.Optional[BaseException]:
        ...

    @classmethod
    @abc.abstractmethod
    def create(
        cls: typing.Type[_SelfT],
        migration_session: session.MigrationSession,
        migration: domain_migration.Migration,
    ) -> _SelfT:
        ...

    @abc.abstractmethod
    def is_failed(self) -> bool:
        ...

    @abc.abstractmethod
    def get_process(
        self, migration: domain_migration.Migration, /
    ) -> domain_migration.MigrationProcess:
        ...

    @abc.abstractmethod
    def apply_to(self, session_context: session.MongoSessionContext) -> None:
        ...

    @abc.abstractmethod
    def commit(
        self,
        migration: domain_migration.Migration,
        mongo_session: session.MongoSessionContext,
    ) -> None:
        ...

    @abc.abstractmethod
    def rollback(
        self,
        migration: domain_migration.Migration,
        mongo_session: session.MongoSessionContext,
    ) -> None:
        ...


class AbstractMigrationTransaction(MigrationTransaction, abc.ABC):
    def __init__(
        self,
        migration_session: session.MigrationSession,
        migration: domain_migration.Migration,
    ) -> None:
        self._client = migration_session.session_client
        self._migration_session = migration_session
        self._migration = migration
        self._exc_val: typing.Optional[BaseException] = None

    @classmethod
    def create(
        cls: typing.Type[_SelfT],
        migration_session: session.MigrationSession,
        migration: domain_migration.Migration,
    ) -> _SelfT:
        return cls(migration_session, migration)  # type: ignore[call-arg]

    @property
    def exc_val(self) -> typing.Optional[BaseException]:
        return self._exc_val

    def is_failed(self) -> bool:
        return self.exc_val is not None

    @typing.final
    def apply_to(self, session_context: session.MongoSessionContext) -> None:
        process = self.get_process(self._migration)
        context = self._build_command_context(session_context)
        validation_service.validate_migration_process(process, context)

        mongodb_session_id = util.hexlify(session_context.mongodb_session_id)
        try:
            waiting_commands_count = len(process.commands)
            with session_context.start_transaction():
                _LOGGER.info(
                    "Beginning a transaction in MongoDB session (%s) for (%s) process.",
                    mongodb_session_id,
                    process.name,
                )

                for command_idx, command in enumerate(process.commands, 1):
                    command.execute(context)

                    _LOGGER.info(
                        "%s command successfully applied (%s of %s).",
                        command.name,
                        command_idx,
                        waiting_commands_count,
                    )

                self.commit(self._migration, session_context)

        except Exception as exc:
            _LOGGER.error(
                "Transaction execution in MongoDB session (%s) ended with error %s.",
                mongodb_session_id,
                type(exc).__name__,
            )
            _LOGGER.error("Error details of transaction execution: %s", str(exc))

            self._exc_val = exc
            self.rollback(self._migration, session_context)

        if session_context.has_ended:
            _LOGGER.info("MongoDB session %s has ended.", mongodb_session_id)

    @typing.final
    def rollback(
        self,
        migration: domain_migration.Migration,
        mongo_session: session.MongoSessionContext,
    ) -> None:
        _LOGGER.debug(
            "Rolling back migration %s with version %s",
            migration.name,
            migration.version,
        )
        self._rollback(migration, mongo_session)

    @typing.final
    def commit(
        self,
        migration: domain_migration.Migration,
        mongo_session: session.MongoSessionContext,
    ) -> None:
        _LOGGER.debug(
            "Committing migration %s with version %s",
            migration.name,
            migration.version,
        )
        self._commit(migration, mongo_session)

    @abc.abstractmethod
    def _rollback(
        self,
        migration: domain_migration.Migration,
        mongo_session: session.MongoSessionContext,
    ) -> None:
        pass

    @abc.abstractmethod
    def _commit(
        self,
        migration: domain_migration.Migration,
        mongo_session: session.MongoSessionContext,
    ) -> None:
        pass

    def _build_command_context(
        self,
        session_context: session.MongoSessionContext,
    ) -> domain_context.MigrationContext:
        return domain_context.MigrationContext(
            mongorunway_session_id=util.hexlify(self._migration_session.session_id),
            mongodb_session_id=util.hexlify(session_context.mongodb_session_id),
            client=self._migration_session.session_client,
            database=self._migration_session.session_database,
        )


class UpgradeTransaction(AbstractMigrationTransaction):
    def get_process(
        self, migration: domain_migration.Migration, /
    ) -> domain_migration.MigrationProcess:
        return migration.upgrade_process

    def _rollback(
        self,
        migration: domain_migration.Migration,
        mongo_session: session.MongoSessionContext,
    ) -> None:
        self._migration_session.set_applied_flag(migration, False)

    def _commit(
        self,
        migration: domain_migration.Migration,
        mongo_session: session.MongoSessionContext,
    ) -> None:
        self._migration_session.set_applied_flag(migration, True)


class DowngradeTransaction(AbstractMigrationTransaction):
    def get_process(
        self, migration: domain_migration.Migration, /
    ) -> domain_migration.MigrationProcess:
        return migration.downgrade_process

    def _rollback(
        self,
        migration: domain_migration.Migration,
        mongo_session: session.MongoSessionContext,
    ) -> None:
        self._migration_session.set_applied_flag(migration, True)

    def _commit(
        self,
        migration: domain_migration.Migration,
        mongo_session: session.MongoSessionContext,
    ) -> None:
        self._migration_session.set_applied_flag(migration, False)
