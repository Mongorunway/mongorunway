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
    "Migration",
    "MigrationProcess",
    "MigrationReadModel",
)

import dataclasses
import typing

if typing.TYPE_CHECKING:
    from mongorunway.domain import migration_business_rule as domain_rule
    from mongorunway.domain import migration_command as domain_command

_ProcessT = typing.TypeVar("_ProcessT", bound="MigrationProcess")


class Migration:
    __slots__: typing.Sequence[str] = (
        "_name",
        "_version",
        "_checksum",
        "_is_applied",
        "_description",
        "_upgrade_process",
        "_downgrade_process",
    )

    def __init__(
        self,
        *,
        name: str,
        version: int,
        checksum: str,
        is_applied: bool,
        description: str,
        upgrade_process: MigrationProcess,
        downgrade_process: MigrationProcess,
    ) -> None:
        self._name = name
        self._version = version
        self._checksum = checksum
        self._is_applied = is_applied
        self._description = description
        self._upgrade_process = upgrade_process
        self._downgrade_process = downgrade_process

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> int:
        return self._version

    @property
    def checksum(self) -> str:
        return self._checksum

    @property
    def description(self) -> str:
        return self._description

    @property
    def is_applied(self) -> bool:
        return self._is_applied

    @property
    def upgrade_process(self) -> MigrationProcess:
        return self._upgrade_process

    @property
    def downgrade_process(self) -> MigrationProcess:
        return self._downgrade_process

    def set_is_applied(self, value: bool, /) -> None:
        self._is_applied = value

    def to_dict(self, *, unique: bool = False) -> typing.Dict[str, typing.Any]:
        mapping = {
            "name": self.name,
            "version": self.version,
            "checksum": self.checksum,
            "is_applied": self.is_applied,
            "description": self.description,
        }

        if unique:
            mapping["_id"] = self.version

        return mapping


@dataclasses.dataclass
class MigrationReadModel:
    name: str
    version: int
    checksum: str
    description: str
    is_applied: bool

    @classmethod
    def from_dict(cls, mapping: typing.MutableMapping[str, typing.Any], /) -> MigrationReadModel:
        mapping.pop("_id", None)  # For mongo records
        return cls(**mapping)

    @classmethod
    def from_migration(cls, migration: Migration, /) -> MigrationReadModel:
        return cls(
            name=migration.name,
            version=migration.version,
            checksum=migration.checksum,
            description=migration.description,
            is_applied=migration.is_applied,
        )


class MigrationProcess:
    def __init__(
        self,
        commands: domain_command.AnyCommandSequence,
        migration_version: int,
        name: str,
    ) -> None:
        self._rules: domain_rule.RuleSequence = []
        self._name = name
        self._commands = commands
        self._migration_version = migration_version

    @property
    def name(self) -> str:
        return self._name

    @property
    def commands(self) -> domain_command.AnyCommandSequence:
        return self._commands

    @property
    def migration_version(self) -> int:
        return self._migration_version

    @property
    def rules(self) -> domain_rule.RuleSequence:
        return self._rules

    def has_rules(self) -> bool:
        return bool(self._rules)

    def add_rule(self: _ProcessT, rule: domain_rule.MigrationBusinessRule, /) -> _ProcessT:
        self._rules.append(rule)
        return self
