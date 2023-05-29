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
