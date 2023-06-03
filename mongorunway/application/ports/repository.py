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

__all__: typing.Sequence[str] = ("MigrationModelRepository",)

import abc
import typing

if typing.TYPE_CHECKING:
    from mongorunway.domain import migration as domain_migration


class MigrationModelRepository(abc.ABC):
    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def __len__(self) -> int:
        ...

    @abc.abstractmethod
    def __contains__(self, item: typing.Any, /) -> bool:
        ...

    @abc.abstractmethod
    def has_migration(self, item: typing.Any, /) -> bool:
        ...

    @abc.abstractmethod
    def has_migration_with_version(self, migration_version: int, /) -> bool:
        ...

    @abc.abstractmethod
    def has_migrations(self) -> bool:
        ...

    @abc.abstractmethod
    def acquire_migration_model_by_version(
        self,
        migration_version: int,
    ) -> typing.Optional[domain_migration.MigrationReadModel]:
        ...

    @abc.abstractmethod
    def acquire_migration_model_by_flag(
        self, is_applied: bool
    ) -> typing.Optional[domain_migration.MigrationReadModel]:
        ...

    @abc.abstractmethod
    def acquire_all_migration_models(
        self,
        *,
        ascending_id: bool = True,
    ) -> typing.Iterator[domain_migration.MigrationReadModel]:
        ...

    @abc.abstractmethod
    def acquire_migration_models_by_flag(
        self, *, is_applied: bool
    ) -> typing.Iterator[domain_migration.MigrationReadModel]:
        ...

    @abc.abstractmethod
    def append_migration(self, migration: domain_migration.Migration, /) -> int:
        ...

    @abc.abstractmethod
    def remove_migration(self, migration_version: int, /) -> int:
        ...

    @abc.abstractmethod
    def set_applied_flag(self, migration: domain_migration.Migration, is_applied: bool) -> int:
        ...
