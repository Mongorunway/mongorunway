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
