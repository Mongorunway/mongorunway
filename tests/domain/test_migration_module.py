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

from mongorunway.domain import migration_business_module as domain_module


@pytest.fixture(scope="function")
def module() -> types.ModuleType:
    return types.ModuleType("my_migration_module")


@pytest.fixture(scope="function")
def migration_module(module: types.ModuleType) -> domain_module.MigrationBusinessModule:
    module.__name__ = "myapp.migrations.my_migration_module"
    module.__file__ = "a/b/c"
    module.__doc__ = "abc"
    module.version = -1
    module.upgrade = lambda: []
    module.downgrade = lambda: []
    return domain_module.MigrationBusinessModule(module)


def test_migration_module(migration_module: domain_module.MigrationBusinessModule) -> None:
    assert migration_module.version == -1
    assert migration_module.location == "a/b/c"
    assert migration_module.description == "abc"
    assert migration_module.get_name() == "my_migration_module"


def test_missing_upgrade_commands(module: types.ModuleType) -> None:
    module.__name__ = "myapp.migrations.my_migration_module"
    module.__file__ = "a/b/c"
    module.__doc__ = "abc"
    module.version = -1
    module.downgrade = lambda: []

    with pytest.raises(
        ValueError, match=f"Can't find 'upgrade' process in 'my_migration_module' migration."
    ):
        domain_module.MigrationBusinessModule(module)


def test_missing_downgrade_commands(module: types.ModuleType) -> None:
    module.__name__ = "myapp.migrations.my_migration_module"
    module.__file__ = "a/b/c"
    module.__doc__ = "abc"
    module.version = -1
    module.upgrade = lambda: []

    with pytest.raises(
        ValueError, match=f"Can't find 'downgrade' process in 'my_migration_module' migration."
    ):
        domain_module.MigrationBusinessModule(module)
