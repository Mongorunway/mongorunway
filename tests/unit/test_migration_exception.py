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

import typing

import pytest

from mongorunway.kernel.domain.migration_exception import (
    MigrationTransactionFailedError,
    NothingToUpgradeError,
    NothingToDowngradeError,
    MigrationFileChangedError,
)

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration import Migration


def test_MigrationTransactionFailedError(migration: Migration) -> None:
    exc = MigrationTransactionFailedError(migration)

    assert exc.migration.version == migration.version

    with pytest.raises(
        MigrationTransactionFailedError,
        match=f"Migration {migration.name!r} with version {migration.version!r} is failed."
    ):
        raise MigrationTransactionFailedError(migration)


def test_NothingToUpgradeError(migration: Migration) -> None:
    exc = MigrationTransactionFailedError(migration)

    assert exc.migration.version == migration.version

    with pytest.raises(NothingToUpgradeError, match="There are currently no pending migrations."):
        raise NothingToUpgradeError()


def test_NothingToDowngradeError(migration: Migration) -> None:
    exc = MigrationTransactionFailedError(migration)

    assert exc.migration.version == migration.version

    with pytest.raises(NothingToDowngradeError, match="There are currently no applied migrations."):
        raise NothingToDowngradeError()


def test_MigrationFileChangedError(migration: Migration) -> None:
    exc = MigrationTransactionFailedError(migration)

    assert exc.migration.version == migration.version

    with pytest.raises(
        MigrationFileChangedError,
        match=f"Migration {migration.name!r} with version {migration.version!r} is changed."
    ):
        raise MigrationFileChangedError(migration)
