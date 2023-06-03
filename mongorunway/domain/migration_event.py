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

import typing

import attr

if typing.TYPE_CHECKING:
    from mongorunway.application import applications

EventHandler: typing.TypeAlias = typing.Callable[["MigrationEvent"], None]

EventHandlerT = typing.TypeVar("EventHandlerT", bound=EventHandler)

EventHandlerProxyOr: typing.TypeAlias = typing.Union[EventHandlerT, "EventHandlerProxy"]


@attr.define(eq=True, order=True, hash=True)
class EventHandlerProxy:
    _priority: int = attr.field(
        eq=True,
        hash=True,
        alias="priority",
    )  # type: ignore[call-overload]

    _handler: EventHandler = attr.field(
        eq=False,
        hash=False,
        alias="handler",
    )  # type: ignore[call-overload]

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
