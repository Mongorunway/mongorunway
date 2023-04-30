from __future__ import annotations

__all__: typing.Sequence[str] = (
    "MigrationHook",
    "PrioritizedMigrationHook",
)

import abc
import typing

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.ui import MigrationUI


class MigrationHook(abc.ABC):
    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def apply(self, application: MigrationUI, /) -> None:
        ...


class PrioritizedMigrationHook(abc.ABC):
    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def __eq__(self, other: typing.Any) -> bool:
        ...

    @abc.abstractmethod
    def __hash__(self) -> int:
        ...

    @property
    @abc.abstractmethod
    def priority(self) -> int:
        ...

    @property
    @abc.abstractmethod
    def item(self) -> MigrationHook:
        ...
