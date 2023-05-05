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

from mongorunway.kernel.application.transactions import UpgradeTransaction, DowngradeTransaction, TRANSACTION_SUCCESS, TRANSACTION_NOT_APPLIED

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration import Migration
    from mongorunway.kernel.application.ui import MigrationUI


def test_constants() -> None:
    assert TRANSACTION_SUCCESS == 1
    assert TRANSACTION_NOT_APPLIED == 0


class TestUpgradeTransaction:
    def test_commit(self, application: MigrationUI, migration: Migration) -> None:
        application.pending.append_migration(migration)
        assert len(application.pending) == 1

        transaction = UpgradeTransaction(application)
        transaction.apply_migration(migration)
        transaction.commit()

        assert len(application.pending) == 0
        assert len(application.applied) == 1

    def test_rollback(self, application: MigrationUI, migration: Migration) -> None:
        application.pending.append_migration(migration)
        assert len(application.pending) == 1

        transaction = UpgradeTransaction(application)

        transaction.apply_migration(migration)
        transaction.commit()

        assert len(application.pending) == 0
        assert len(application.applied) == 1

        transaction.rollback()

        assert len(application.pending) == 1
        assert len(application.applied) == 0

    def test_ensure_migration(self, application: MigrationUI, migration: Migration) -> None:
        application.pending.append_migration(migration)
        assert len(application.pending) == 1

        transaction = UpgradeTransaction(application)
        transaction.apply_migration(migration)

        assert transaction.ensure_migration().version == migration.version


class TestDowngradeTransaction:
    def test_commit(self, application: MigrationUI, migration: Migration) -> None:
        application.applied.append_migration(migration)
        assert len(application.applied) == 1

        transaction = DowngradeTransaction(application)
        transaction.apply_migration(migration)
        transaction.commit()

        assert len(application.applied) == 0
        assert len(application.pending) == 1

    def test_rollback(self, application: MigrationUI, migration: Migration) -> None:
        application.applied.append_migration(migration)
        assert len(application.applied) == 1

        transaction = DowngradeTransaction(application)

        transaction.apply_migration(migration)
        transaction.commit()

        assert len(application.applied) == 0
        assert len(application.pending) == 1

        transaction.rollback()

        assert len(application.applied) == 1
        assert len(application.pending) == 0

    def test_ensure_migration(self, application: MigrationUI, migration: Migration) -> None:
        application.applied.append_migration(migration)
        assert len(application.applied) == 1

        transaction = DowngradeTransaction(application)
        transaction.apply_migration(migration)

        assert transaction.ensure_migration().version == migration.version
