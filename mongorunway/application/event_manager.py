from __future__ import annotations

import collections
import inspect
import heapq
import operator
import typing

from mongorunway.domain import migration_event_manager as domain_event_manager
from mongorunway.domain import migration_event as domain_event


class MigrationEventManagerImpl(domain_event_manager.MigrationEventManager):
    __slots__: typing.Sequence[str] = ("_event_dict", "_event_cond")

    def __init__(self) -> None:
        self._event_dict: typing.DefaultDict[
            typing.Type[domain_event.MigrationEvent],
            typing.MutableSequence[domain_event.EventHandlerProxyOr[domain_event.EventHandler]],
        ] = collections.defaultdict(list)

    def subscribe_events(
        self,
        handler: domain_event.EventHandlerProxyOr[domain_event.EventHandler],
        *events: typing.Type[domain_event.MigrationEvent],
    ) -> None:
        for event in events:
            self.subscribe_event_handler(handler, event)

    def unsubscribe_events(self, *events: typing.Type[domain_event.MigrationEvent]) -> None:
        for event in events:
            self._event_dict.pop(event)

    def subscribe_event_handler(
        self,
        handler: domain_event.EventHandlerProxyOr[domain_event.EventHandler],
        event: typing.Type[domain_event.MigrationEvent],
    ) -> None:
        self._event_dict[event].append(handler)

    def unsubscribe_event_handler(
        self,
        handler: domain_event.EventHandlerProxyOr[domain_event.EventHandler],
        event: typing.Type[domain_event.MigrationEvent],
    ) -> None:
        self._event_dict[event].remove(handler)

    def get_event_handlers_for(
        self, event: typing.Type[domain_event.MigrationEvent],
    ) -> typing.MutableSequence[domain_event.EventHandlerProxyOr[domain_event.EventHandler]]:
        return self._event_dict[event]

    def prioritize_handler(
        self,
        handler: domain_event.EventHandler,
        event: typing.Type[domain_event.MigrationEvent],
        priority: int,
    ) -> None:
        handlers = self.get_event_handlers_for(event)

        try:
            index = handlers.index(handler)
        except ValueError:
            raise ValueError(
                f"Handler {handler!r} is not subscribed for {event!r}."
            )

        handlers.remove(handler)
        handlers.insert(
            index,
            domain_event.EventHandlerProxy(
                handler=handler,
                priority=priority,
            )
        )

    def unprioritize_handler_proxy(
        self,
        handler_proxy: domain_event.EventHandlerProxy,
        event: typing.Type[domain_event.MigrationEvent]
    ) -> None:
        handlers = self._event_dict[event]

        try:
            index = handlers.index(handler_proxy)
        except ValueError:
            raise ValueError(
                f"Handler {handler_proxy!r} is not subscribed for {event!r}."
            )

        handlers.remove(handler_proxy)
        handlers.insert(index, handler_proxy.handler)

    def listen(
        self,
        *events: typing.Type[domain_event.MigrationEvent],
    ) -> typing.Callable[[domain_event.EventHandlerT], domain_event.EventHandlerT]:
        def decorator(
            handler: domain_event.EventHandlerProxyOr[domain_event.EventHandlerT],
        ) -> domain_event.EventHandlerProxyOr[domain_event.EventHandlerT]:
            handler_func = handler
            if isinstance(handler, domain_event.EventHandlerProxy):
                handler_func = handler.handler

            if not events:
                signature = inspect.signature(handler_func, eval_str=True)
                try:
                    parameter = signature.parameters["event"]
                    if parameter.annotation is inspect.Parameter.empty:
                        raise
                except KeyError as exc:
                    raise ValueError(
                        f"Handler missing 'event' parameter or parameter annotation."
                    ) from exc

                if typing.get_origin(parameter.annotation) is typing.Union:
                    self.subscribe_events(handler, *typing.get_args(parameter.annotation))
                    return handler

                self.subscribe_events(handler, parameter.annotation)
                return handler

            self.subscribe_events(handler, *events)
            return handler

        return decorator

    def dispatch(self, event: domain_event.MigrationEvent) -> None:
        handlers = self.get_event_handlers_for(type(event))
        prioritized_handlers = []
        unprioritized_handlers = []

        for handler in handlers:
            if isinstance(handler, domain_event.EventHandlerProxy):
                prioritized_handlers.append(handler)
            else:
                unprioritized_handlers.append(handler)

        prioritized_handlers.sort(key=operator.attrgetter("priority"))
        heapq.heapify(prioritized_handlers)

        while prioritized_handlers:
            proxy = heapq.heappop(prioritized_handlers)
            proxy.handler(event)

        for handler in unprioritized_handlers:
            handler(event)
