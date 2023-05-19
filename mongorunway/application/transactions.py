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

from mongorunway import mongo
from mongorunway import util

if typing.TYPE_CHECKING:
    from mongorunway.application import session
    from mongorunway.domain import migration as domain_migration

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("mongorunway.transactions")
_SelfT = typing.TypeVar("_SelfT", bound="MigrationTransaction")

TransactionCode: typing.TypeAlias = int

TRANSACTION_SUCCESS: typing.Final[TransactionCode] = 1
"""An integer constant indicating that a transaction has been successfully applied."""

TRANSACTION_NOT_APPLIED: typing.Final[TransactionCode] = 0
"""An integer constant indicating that a transaction has not been applied."""


class MigrationTransaction(abc.ABC):
    """Abstract base class for implementing migration transactions."""

    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def exc_val(self) -> typing.Optional[BaseException]:
        ...

    @classmethod
    @abc.abstractmethod
    def create(cls: typing.Type[_SelfT], migration_session: session.MigrationSession) -> _SelfT:
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
    def apply(self, migration: domain_migration.Migration) -> None:
        """
        Apply the given migration to the database.

        Parameters
        ----------
        migration : Migration
            The migration to apply.
        """
        ...

    @abc.abstractmethod
    def commit(
        self,
        migration: domain_migration.Migration,
        mongo_session: mongo.ClientSession,
    ) -> None:
        """Commit the transaction."""
        ...

    @abc.abstractmethod
    def rollback(
        self,
        migration: domain_migration.Migration,
        mongo_session: mongo.ClientSession,
    ) -> None:
        """Rollback the transaction."""
        ...

    @abc.abstractmethod
    def ensure_migration(self) -> domain_migration.Migration:
        ...


class AbstractMigrationTransaction(MigrationTransaction, abc.ABC):
    def __init__(self, migration_session: session.MigrationSession) -> None:
        self.client = migration_session.session_config.application.app_client
        self.migration_session = migration_session

        self._migration: typing.Optional[domain_migration.Migration] = None
        self._exc_val: typing.Optional[BaseException] = None

    @classmethod
    def create(cls: typing.Type[_SelfT], migration_session: session.MigrationSession) -> _SelfT:
        return cls(migration_session)  # type: ignore[call-arg]

    @property
    def exc_val(self) -> typing.Optional[BaseException]:
        return self._exc_val

    def is_failed(self) -> bool:
        return self.exc_val is not None

    @typing.final
    def apply(self, migration: domain_migration.Migration) -> None:
        self._migration = migration

        process = self.get_process(migration)
        with self.client.start_session() as mongo_session:
            session_id = util.hexlify(mongo_session.session_id["id"])
            _LOGGER.info("Connected to MongoDB session (%s)", session_id)

            self.migration_session.validate_migration_process(
                process,
                mongo_session.client,
            )

            try:
                with mongo_session.start_transaction():
                    _LOGGER.info(
                        "Beginning a transaction in session (%s) for (%s) process.",
                        session_id,
                        process.name,
                    )

                    for command in process.commands:
                        _LOGGER.info("Executing %s command...", command.name)
                        command.execute(self.client)

                    self.commit(migration, mongo_session)

            except Exception as exc:
                _LOGGER.error(
                    "Transaction execution in session (%s) ended with error %s.",
                    session_id,
                    type(exc).__name__,
                )
                _LOGGER.debug("Error details of transaction execution: %s", str(exc))

                self._exc_val = exc
                self.rollback(migration, mongo_session)

        if mongo_session.has_ended:
            _LOGGER.info("MongoDB session %s has ended.", session_id)

    @typing.final
    def rollback(
        self,
        migration: domain_migration.Migration,
        mongo_session: mongo.ClientSession,
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
        mongo_session: mongo.ClientSession,
    ) -> None:
        _LOGGER.debug(
            "Committing migration %s with version %s",
            migration.name,
            migration.version,
        )
        self._commit(migration, mongo_session)

    @typing.final
    def ensure_migration(self) -> domain_migration.Migration:
        if self._migration is None:
            raise ValueError("Migration is not applied to current transaction.")

        return self._migration

    @abc.abstractmethod
    def _rollback(
        self,
        migration: domain_migration.Migration,
        mongo_session: mongo.ClientSession,
    ) -> None:
        pass

    @abc.abstractmethod
    def _commit(
        self,
        migration: domain_migration.Migration,
        mongo_session: mongo.ClientSession,
    ) -> None:
        pass


class UpgradeTransaction(AbstractMigrationTransaction):
    def get_process(
        self, migration: domain_migration.Migration, /
    ) -> domain_migration.MigrationProcess:
        return migration.upgrade_process

    def _rollback(
        self,
        migration: domain_migration.Migration,
        mongo_session: mongo.ClientSession,
    ) -> None:
        mongo_session.abort_transaction()
        self.migration_session.set_applied_flag(migration, False)

    def _commit(
        self,
        migration: domain_migration.Migration,
        mongo_session: mongo.ClientSession,
    ) -> None:
        mongo_session.commit_transaction()
        self.migration_session.set_applied_flag(migration, True)


class DowngradeTransaction(AbstractMigrationTransaction):
    def get_process(
        self, migration: domain_migration.Migration, /
    ) -> domain_migration.MigrationProcess:
        return migration.downgrade_process

    def _rollback(
        self,
        migration: domain_migration.Migration,
        mongo_session: mongo.ClientSession,
    ) -> None:
        mongo_session.abort_transaction()
        self.migration_session.set_applied_flag(migration, True)

    def _commit(
        self,
        migration: domain_migration.Migration,
        mongo_session: mongo.ClientSession,
    ) -> None:
        mongo_session.commit_transaction()
        self.migration_session.set_applied_flag(migration, False)
