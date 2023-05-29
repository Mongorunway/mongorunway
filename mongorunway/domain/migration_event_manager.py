from __future__ import annotations

import abc
import typing

if typing.TYPE_CHECKING:
    from mongorunway.domain import migration_event as domain_event


class MigrationEventManager(abc.ABC):
    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def subscribe_events(
        self,
        handler: domain_event.EventHandlerProxyOr[domain_event.EventHandler],
        *events: typing.Type[domain_event.MigrationEvent],
    ) -> None:
        ...

    @abc.abstractmethod
    def unsubscribe_events(self, event: typing.Type[domain_event.MigrationEvent]) -> None:
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
        self, event: typing.Type[domain_event.MigrationEvent],
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
        domain_event.EventHandlerProxyOr[domain_event.EventHandlerT]
    ]:
        ...

    @abc.abstractmethod
    def dispatch(self, event: domain_event.MigrationEvent) -> None:
        ...
