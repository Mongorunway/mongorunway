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
from unittest.mock import Mock

import pymongo

from mongorunway.kernel.domain.migration_command import MigrationCommand
from mongorunway.kernel.infrastructure.migrations import BaseMigration


class FakeCommand(MigrationCommand):
    def execute(self, conn: pymongo.MongoClient[typing.Dict[str, typing.Any]]) -> None:
        pass


def test_base_migration() -> None:
    migration = BaseMigration(
        version=1,
        name="abc",
        checksum="abc",
        description="abc",
        upgrade_commands=[Mock(), Mock()],
        downgrade_commands=[Mock(), Mock()],
    )

    assert len(migration.downgrade_commands) == 2
    assert len(migration.upgrade_commands) == 2

    mock_client = Mock(spec=pymongo.MongoClient)

    migration.upgrade(mock_client)
    for command in migration.upgrade_commands:
        command.execute.assert_called_once_with(mock_client)

    migration.downgrade(mock_client)
    for command in migration.downgrade_commands:
        command.execute.assert_called_once_with(mock_client)
