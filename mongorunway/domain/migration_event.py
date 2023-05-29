from __future__ import annotations

import typing

import attr

if typing.TYPE_CHECKING:
    from mongorunway.application import applications

EventHandler: typing.TypeAlias = typing.Callable[["MigrationEvent"], None]

EventHandlerT = typing.TypeVar("EventHandlerT", bound=EventHandler)

EventHandlerProxyOr: typing.TypeAlias = typing.Union[EventHandlerT, "EventHandlerProxy"]


@attr.define(eq=True, order=True, hash=True)
class EventHandlerProxy:
    _priority: int = attr.field(eq=True, hash=True, alias="priority")

    _handler: EventHandler = attr.field(eq=False, hash=False, alias="handler")

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def handler(self) -> EventHandler:
        return self._handler

    def __call__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        self._handler(*args, **kwargs)


@attr.define
class MigrationEvent:
    pass


@attr.define
class ApplicationEvent(MigrationEvent):
    application: applications.MigrationApp = attr.field()


@attr.define
class StartingEvent(ApplicationEvent):
    pass
