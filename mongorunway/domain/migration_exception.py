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
"""This module defines a hierarchy of exceptions used throughout the migration application."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "MigrationError",
    "MigrationFailedError",
    "MigrationTransactionFailedError",
    "NothingToUpgradeError",
    "NothingToDowngradeError",
    "MigrationHookError",
    "MigrationFileChangedError",
)

import typing

if typing.TYPE_CHECKING:
    from mongorunway.domain import migration as domain_migration
    from mongorunway.domain import migration_business_rule as domain_rule


class MigrationError(Exception):
    """Base class for all migration errors.

    This class is inherited by all other migration-related exception classes.
    """

    __slots__: typing.Sequence[str] = ()

    pass


class MigrationFailedError(MigrationError):
    """Error that is raised when a migration fails to apply.

    This exception is raised when a migration command fails to execute properly.
    """

    __slots__: typing.Sequence[str] = ()

    pass


class MigrationBusinessRuleBrokenError(Exception):

    __slots__ = ("rule",)

    def __init__(self, rule: domain_rule.MigrationBusinessRule) -> None:
        super().__init__(rule.render_broken_rule())
        self.rule = rule


class MigrationTransactionFailedError(MigrationFailedError):
    """Raised when a migration transaction fails.

    This exception is raised when a transaction of a migration fails during execution.

    Parameters
    ----------
    migration : Migration
        The migration that caused the error.
    """

    __slots__: typing.Sequence[str] = ("failed_migration",)

    def __init__(self, migration: domain_migration.Migration, /) -> None:
        self.failed_migration = migration

        super().__init__(
            f"Migration {migration.name!r} with version {migration.version!r} is failed."
        )


class NothingToUpgradeError(MigrationFailedError):
    """An exception raised when there are no pending migrations to upgrade."""

    __slots__: typing.Sequence[str] = ()

    def __str__(self) -> str:
        return "There are currently no pending migrations."


class NothingToDowngradeError(MigrationFailedError):
    """An exception raised when there are no applied migrations to downgrade."""

    __slots__: typing.Sequence[str] = ()

    def __str__(self) -> str:
        return "There are currently no applied migrations."


class MigrationHookError(MigrationError):
    """Base error occurred while executing a migration hook."""

    __slots__: typing.Sequence[str] = ()

    pass


class MigrationFileChangedError(MigrationHookError):
    """Exception raised when a migration file is changed.

    This exception is raised when a migration file is modified after it has been
    applied to the database.

    Parameters
    ----------
    migration : Migration
        The migration that caused the error.
    """

    __slots__: typing.Sequence[str] = (
        "failed_migration_name",
        "failed_migration_version",
    )

    def __init__(self, migration_name: str, migration_version: int) -> None:
        self.failed_migration_name = migration_name
        self.failed_migration_version = migration_version

        super().__init__(
            f"Migration {migration_name!r} with version {migration_version!r} is changed."
        )
