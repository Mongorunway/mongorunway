from __future__ import annotations

__all__ = ("MigrationBusinessRule", "AbstractMigrationBusinessRule")

import abc
import typing

if typing.TYPE_CHECKING:
    from mongorunway import mongo

RuleSequence: typing.TypeAlias = typing.MutableSequence["MigrationBusinessRule"]


class MigrationBusinessRule(abc.ABC):
    __slots__ = ()

    @property
    @abc.abstractmethod
    def name(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def depends_on(self) -> typing.Sequence[MigrationBusinessRule]:
        ...

    @abc.abstractmethod
    def is_independent(self) -> bool:
        ...

    @abc.abstractmethod
    def check_is_broken(self, client: mongo.Client) -> bool:
        ...

    @abc.abstractmethod
    def render_broken_rule(self) -> str:
        ...


class AbstractMigrationBusinessRule(MigrationBusinessRule, abc.ABC):
    def __init__(self, depends_on: typing.Sequence[MigrationBusinessRule] = ()) -> None:
        self._depends_on = depends_on

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def depends_on(self) -> typing.Sequence[MigrationBusinessRule]:
        return self._depends_on

    def is_independent(self) -> bool:
        return not self._depends_on

    def render_broken_rule(self) -> str:
        return f"Business rule {self.name} is broken."
