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
    "MigrationBusinessRule",
    "AbstractMigrationBusinessRule",
)

import abc
import typing

if typing.TYPE_CHECKING:
    from mongorunway import mongo
    from mongorunway.domain import migration_context as domain_context

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
    def check_is_broken(self, ctx: domain_context.MigrationContext) -> bool:
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
