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

__all__: typing.Sequence[str] = ("MigrationBusinessModule",)

import types
import typing

from mongorunway.domain import migration as domain_migration


class MigrationBusinessModule:
    __slots__: typing.Sequence[str] = (
        "_module",
        "_upgrade_process",
        "_downgrade_process",
    )

    def __init__(self, module: types.ModuleType, /) -> None:
        self._module = module
        self._upgrade_process = self._get_business_process("upgrade")
        self._downgrade_process = self._get_business_process("downgrade")

    @property
    def location(self) -> str:
        return self._module.__file__ or ""

    @property
    def description(self) -> str:
        return self._module.__doc__ or ""

    @property
    def version(self) -> int:
        return typing.cast(int, self._module.version)

    @property
    def upgrade_process(self) -> domain_migration.MigrationProcess:
        return self._upgrade_process

    @property
    def downgrade_process(self) -> domain_migration.MigrationProcess:
        return self._downgrade_process

    def get_name(self) -> str:
        *_, migration_name = self._module.__name__.split(".")
        return migration_name.strip()

    def _get_business_process(self, process_name: str, /) -> domain_migration.MigrationProcess:
        process = getattr(self._module, process_name, None)
        if process is None:
            raise ValueError(
                f"Can't find {process_name!r} process in {self.get_name()!r} migration."
            )

        return process
