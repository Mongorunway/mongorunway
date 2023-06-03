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
    from mongorunway.application import session
    from mongorunway.domain import migration as domain_migration
    from mongorunway.domain import migration_event_manager as domain_event_manager


class MigrationSessionAware(abc.ABC):
    @property
    @abc.abstractmethod
    def session(self) -> session.MigrationSession:
        ...


class MigrationEventManagerAware(abc.ABC):
    @property
    @abc.abstractmethod
    def event_manager(self) -> domain_event_manager.MigrationEventManager:
        ...


class MigrationRunner(abc.ABC):
    __slots__ = ()

    @abc.abstractmethod
    def upgrade_once(self) -> int:
        ...

    @abc.abstractmethod
    def downgrade_once(self) -> int:
        ...

    @abc.abstractmethod
    def upgrade_while(
        self, predicate: typing.Callable[[domain_migration.Migration], bool], /
    ) -> int:
        ...

    @abc.abstractmethod
    def downgrade_while(
        self, predicate: typing.Callable[[domain_migration.Migration], bool], /
    ) -> int:
        ...

    @abc.abstractmethod
    def downgrade_to(self, migration_version: int, /) -> int:
        ...

    @abc.abstractmethod
    def upgrade_to(self, migration_version: int, /) -> int:
        ...

    @abc.abstractmethod
    def downgrade_all(self) -> int:
        ...

    @abc.abstractmethod
    def upgrade_all(self) -> int:
        ...
