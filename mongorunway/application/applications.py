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
    "MigrationApp",
    "MigrationAppImpl",
)

import abc
import functools
import logging
import typing

from mongorunway.application import event_manager
from mongorunway.application import session
from mongorunway.application import traits
from mongorunway.application import transactions
from mongorunway.application import ux
from mongorunway.application.services import migration_service
from mongorunway.application.services import versioning_service
from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_event as domain_event
from mongorunway.domain import migration_exception as domain_exception

if typing.TYPE_CHECKING:
    from mongorunway.application import config
    from mongorunway.domain import migration_event_manager as domain_event_manager

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
                if self.session.raises_on_transaction_failure:
                    if is_applied:
                        raise domain_exception.NothingToDowngradeError()
                    raise domain_exception.NothingToUpgradeError()

                return typing.cast(
                    _TransactionCodeT,
                    transactions.TRANSACTION_NOT_APPLIED,
                )
            return meth(*args, **kwargs)

        return wrapper

    return decorator


class MigrationApp(
    traits.MigrationRunner,
    traits.MigrationSessionAware,
    traits.MigrationEventManagerAware,
    abc.ABC,
):
    __slots__: typing.Sequence[str] = ()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        ...

    @abc.abstractmethod
    def subscribe_events(
        self,
        handler: domain_event.EventHandlerProxyOr[domain_event.EventHandler],
        *events: typing.Type[domain_event.MigrationEvent],
    ) -> None:
        ...

    @abc.abstractmethod
    def unsubscribe_events(self, *events: typing.Type[domain_event.MigrationEvent]) -> None:
        ...

    @abc.abstractmethod
    def subscribe_event_handler(
        self,
        handler: domain_event.EventHandlerProxyOr[domain_event.EventHandler],
        event: typing.Type[domain_event.MigrationEvent],
    ) -> None:
        ...

    @abc.abstractmethod
    def unsubscribe_event_handler(
        self,
        handler: domain_event.EventHandlerProxyOr[domain_event.EventHandler],
        event: typing.Type[domain_event.MigrationEvent],
    ) -> None:
        ...

    @abc.abstractmethod
    def get_event_handlers_for(
        self,
        event: typing.Type[domain_event.MigrationEvent],
    ) -> typing.MutableSequence[domain_event.EventHandlerProxyOr[domain_event.EventHandler]]:
        ...

    @abc.abstractmethod
    def prioritize_handler(
        self,
        handler: domain_event.EventHandler,
        event: typing.Type[domain_event.MigrationEvent],
        priority: int,
    ) -> None:
        ...

    @abc.abstractmethod
    def unprioritize_handler_proxy(
        self,
        handler_proxy: domain_event.EventHandlerProxy,
        event: typing.Type[domain_event.MigrationEvent],
    ) -> None:
        ...

    @abc.abstractmethod
    def listen(
        self,
        *events: typing.Type[domain_event.MigrationEvent],
    ) -> typing.Callable[
        [domain_event.EventHandlerProxyOr[domain_event.EventHandlerT]],
        domain_event.EventHandlerProxyOr[domain_event.EventHandlerT],
    ]:
        ...

    @abc.abstractmethod
    def dispatch(self, event: domain_event.MigrationEvent) -> None:
        ...


class MigrationAppImpl(MigrationApp):
    __slots__: typing.Sequence[str] = (
        "_config",
        "_session",
        "_event_manager",
        "_migration_service",
    )

    def __init__(
        self,
        configuration: config.Config,
    ) -> None:
        ux.init_logging(configuration)
        ux.init_components(configuration)

        self._session = app_session = session.MigrationSessionImpl(self, configuration)
        self._migration_service = migration_service.MigrationService(app_session)

        self._event_manager = event_manager.MigrationEventManagerImpl()
        for event_type, event_handlers in configuration.application.app_subscribed_events.items():
            for handler in event_handlers:
                self._event_manager.subscribe_event_handler(handler, event_type)

        self._event_manager.dispatch(domain_event.StartingEvent(self))

    @property
    def name(self) -> str:
        return self._session.session_name

    @property
    def session(self) -> session.MigrationSession:
        return self._session

    @property
    def event_manager(self) -> domain_event_manager.MigrationEventManager:
        return self._event_manager

    def subscribe_events(
        self,
        handler: domain_event.EventHandlerProxyOr[domain_event.EventHandler],
        *events: typing.Type[domain_event.MigrationEvent],
    ) -> None:
        return self._event_manager.subscribe_events(handler, *events)

    def unsubscribe_events(self, *events: typing.Type[domain_event.MigrationEvent]) -> None:
        return self._event_manager.unsubscribe_events(*events)

    def subscribe_event_handler(
        self,
        handler: domain_event.EventHandlerProxyOr[domain_event.EventHandler],
        event: typing.Type[domain_event.MigrationEvent],
    ) -> None:
        return self._event_manager.subscribe_event_handler(handler, event)

    def unsubscribe_event_handler(
        self,
        handler: domain_event.EventHandlerProxyOr[domain_event.EventHandler],
        event: typing.Type[domain_event.MigrationEvent],
    ) -> None:
        return self._event_manager.unsubscribe_event_handler(handler, event)

    def get_event_handlers_for(
        self,
        event: typing.Type[domain_event.MigrationEvent],
    ) -> typing.MutableSequence[domain_event.EventHandlerProxyOr[domain_event.EventHandler]]:
        return self._event_manager.get_event_handlers_for(event)

    def prioritize_handler(
        self,
        handler: domain_event.EventHandler,
        event: typing.Type[domain_event.MigrationEvent],
        priority: int,
    ) -> None:
        return self._event_manager.prioritize_handler(handler, event, priority)

    def unprioritize_handler_proxy(
        self,
        handler_proxy: domain_event.EventHandlerProxy,
        event: typing.Type[domain_event.MigrationEvent],
    ) -> None:
        return self._event_manager.unprioritize_handler_proxy(handler_proxy, event)

    def listen(
        self,
        *events: typing.Type[domain_event.MigrationEvent],
    ) -> typing.Callable[
        [domain_event.EventHandlerProxyOr[domain_event.EventHandlerT]],
        domain_event.EventHandlerProxyOr[domain_event.EventHandlerT],
    ]:
        return self._event_manager.listen(*events)

    def dispatch(self, event: domain_event.MigrationEvent) -> None:
        return self._event_manager.dispatch(event)

    @requires_migrations(is_applied=False)
    def upgrade_once(self) -> int:
        pending_migration_model = self._session.get_migration_model_by_flag(is_applied=False)
        assert pending_migration_model is not None  # Only for type checkers

        pending_migration = self._migration_service.get_migration(
            pending_migration_model.name,
            pending_migration_model.version,
        )

        with self._session.begin_mongo_session() as session_context:
            _LOGGER.info(
                "%s: upgrading waiting migration (#%s -> #%s)...",
                self.name,
                versioning_service.get_previous_migration_version(pending_migration),
                pending_migration.version,
            )

            with self._session.begin_transaction(
                transactions.UpgradeTransaction,
                migration=pending_migration,
            ) as transaction:
                transaction.apply_to(session_context)

                _LOGGER.info(
                    "%s: Successfully upgraded to (#%s).",
                    self.name,
                    pending_migration.version,
                )
                return transactions.TRANSACTION_SUCCESS

    @requires_migrations(is_applied=True)
    def downgrade_once(self) -> int:
        applied_migration_model = self._session.get_migration_model_by_flag(is_applied=True)
        assert applied_migration_model is not None  # Only for type checkers

        applied_migration = self._migration_service.get_migration(
            applied_migration_model.name,
            applied_migration_model.version,
        )

        with self._session.begin_mongo_session() as session_context:
            _LOGGER.info(
                "%s: downgrading waiting migration (#%s -> #%s)...",
                self.name,
                applied_migration.version,
                versioning_service.get_previous_migration_version(applied_migration),
            )

            with self._session.begin_transaction(
                transactions.DowngradeTransaction,
                migration=applied_migration,
            ) as transaction:
                transaction.apply_to(session_context)

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
        upgraded = 0
        pending_migration_models = self._session.get_migration_models_by_flag(is_applied=False)

        with self._session.begin_mongo_session() as session_context:
            while pending_migration_models:
                migration = self._migration_service.get_migration(
                    (model := pending_migration_models.pop(0)).name,
                    model.version,
                )

                if not predicate(migration):
                    break

                _LOGGER.info(
                    "%s: upgrading waiting migration (#%s -> #%s)...",
                    self.name,
                    versioning_service.get_previous_migration_version(migration),
                    migration.version,
                )

                with self._session.begin_transaction(
                    transactions.UpgradeTransaction,
                    migration=migration,
                ) as transaction:
                    transaction.apply_to(session_context)

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
        downgraded = 0
        applied_migration_models = self._session.get_migration_models_by_flag(is_applied=True)

        with self._session.begin_mongo_session() as session_context:
            while applied_migration_models:
                migration = self._migration_service.get_migration(
                    (model := applied_migration_models.pop(0)).name,
                    model.version,
                )

                if not predicate(migration):
                    break

                _LOGGER.info(
                    "%s: downgrading waiting migration (#%s -> #%s)...",
                    self.name,
                    migration.version,
                    versioning_service.get_previous_migration_version(migration),
                )

                with self._session.begin_transaction(
                    transactions.DowngradeTransaction,
                    migration=migration,
                ) as transaction:
                    transaction.apply_to(session_context)

                _LOGGER.info(
                    "%s: successfully downgraded to (#%s).",
                    self.name,
                    versioning_service.get_previous_migration_version(migration),
                )
                downgraded += 1

            return downgraded

    def downgrade_to(self, migration_version: int, /) -> int:
        if not migration_version:
            return self.downgrade_all()

        model = self.session.get_migration_model_by_version(migration_version)
        if model is None:
            raise ValueError(f"Migration with version {migration_version!r} is not found.")

        if not model.is_applied:
            raise ValueError(f"Migration with version {migration_version} is already pending.")

        return self.downgrade_while(lambda m: m.version > migration_version)

    def upgrade_to(self, migration_version: int, /) -> int:
        model = self.session.get_migration_model_by_version(migration_version)
        if model is None:
            raise ValueError(f"Migration with version {migration_version!r} is not found.")

        if model.is_applied:
            raise ValueError(f"Migration with version {migration_version} is already applied.")

        return self.upgrade_while(lambda m: m.version <= migration_version)

    def downgrade_all(self) -> int:
        return self.downgrade_while(lambda _: True)

    def upgrade_all(self) -> int:
        return self.upgrade_while(lambda _: True)
