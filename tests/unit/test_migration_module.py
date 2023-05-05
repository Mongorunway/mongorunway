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

import types

import pytest

from mongorunway.kernel.domain.migration_module import MigrationModule


@pytest.fixture(scope="function")
def module() -> types.ModuleType:
    return types.ModuleType("my_migration_module")


def test_migration_module(module: types.ModuleType) -> None:
    module.__name__ = "myapp.migrations.my_migration_module"
    module.__file__ = "a/b/c"
    module.__doc__ = "abc"
    module.version = -1
    module.upgrade = lambda: []
    module.downgrade = lambda: []

    migration_module = MigrationModule(module)

    assert migration_module.version == -1
    assert migration_module.location == "a/b/c"
    assert migration_module.description == "abc"
    assert migration_module.get_name() == "my_migration_module"
    assert migration_module.get_upgrade_commands() == []
    assert migration_module.get_downgrade_commands() == []


def test_missing_upgrade_commands(module: types.ModuleType) -> None:
    module.downgrade = lambda: []

    with pytest.raises(ValueError, match="missing requirement function: 'upgrade'"):
        MigrationModule(module)


def test_missing_downgrade_commands(module: types.ModuleType) -> None:
    module.upgrade = lambda: []

    with pytest.raises(ValueError, match="missing requirement function: 'downgrade'"):
        MigrationModule(module)


def test_upgrade_is_not_callable(module: types.ModuleType) -> None:
    module.upgrade = 1
    module.downgrade = lambda: []

    with pytest.raises(ValueError, match="Object '1' is not callable."):
        MigrationModule(module)


def test_downgrade_is_not_callable(module: types.ModuleType) -> None:
    module.upgrade = lambda: []
    module.downgrade = 1

    with pytest.raises(ValueError, match="Object '1' is not callable."):
        MigrationModule(module)


def test_upgrade_does_not_returns_sequence(module: types.ModuleType) -> None:
    module.upgrade = lambda: 1
    module.downgrade = lambda: []

    with pytest.raises(ValueError, match="'upgrade' function must return sequence of commands."):
        MigrationModule(module).get_upgrade_commands()


def test_downgrade_does_not_returns_sequence(module: types.ModuleType) -> None:
    module.upgrade = lambda: []
    module.downgrade = lambda: 1

    with pytest.raises(ValueError, match="'downgrade' function must return sequence of commands."):
        MigrationModule(module).get_downgrade_commands()
