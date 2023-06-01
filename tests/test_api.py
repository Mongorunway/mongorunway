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

import pathlib
import types
import typing

import pytest

from mongorunway.api import create_app
from mongorunway.api import migration
from mongorunway.api import migration_with_rule
from mongorunway.api import raise_if_migration_version_mismatch
from mongorunway.application import applications
from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_business_rule as domain_rule

if typing.TYPE_CHECKING:
    from mongorunway.application import config


class FakeRule(domain_rule.AbstractMigrationBusinessRule):
    def check_is_broken(self, client: typing.Any) -> bool:
        ...

    def render_broken_rule(self) -> str:
        ...


def dummy_func() -> None:
    pass


def func_returning_empty_sequence() -> typing.Sequence[typing.Any]:
    return ()


def func_returning_migration_process() -> domain_migration.MigrationProcess:
    return domain_migration.MigrationProcess(
        commands=[],
        name="ABC",
        migration_version=1,
    )


def test_migration_with_rule() -> None:
    process = func_returning_migration_process()
    assert len(process.rules) == 0

    migration_with_rule(FakeRule())(process)
    assert len(process.rules) == 1

    with pytest.raises(ValueError):
        migration_with_rule(123)(process)


@pytest.mark.parametrize(
    "process_func, should_raise",
    [
        (func_returning_migration_process, False),
        (dummy_func, True),
        (func_returning_empty_sequence, True),  # Func module must have version constant
    ],
)
def test_migration(process_func: types.FunctionType, should_raise: bool) -> None:
    if should_raise:
        with pytest.raises(ValueError):
            migration(process_func)
    else:
        assert isinstance(migration(process_func), domain_migration.MigrationProcess)


@pytest.mark.parametrize(
    "current_version, expected_version, should_raise",
    [
        (0, 0, False),
        (0, 1, True),
        (0, lambda: 1, True),
    ],
)
def test_raise_if_migration_version_mismatch(
    application: applications.MigrationApp,
    current_version: int,
    expected_version: int,
    should_raise: bool,
) -> None:
    application.session.get_current_version = lambda: current_version

    if should_raise:
        with pytest.raises(ValueError):
            raise_if_migration_version_mismatch(application, expected_version)
    else:
        raise_if_migration_version_mismatch(application, expected_version)


class TestCreateApp:
    def test_configuration_parameter(
        self,
        application: applications.MigrationApp,
        configuration: config.Config,
        tmp_path: pathlib.Path,
    ) -> None:
        app = create_app(application.name, configuration=configuration)
        assert isinstance(app, applications.MigrationApp)

        assert (tmp_path / "mongorunway.yaml").write_text("mongorunway")
        app = create_app(application.name, configuration=tmp_path)
        assert app is None

    def test_raise_on_none(
        self,
        application: applications.MigrationApp,
        configuration: config.Config,
        tmp_path: pathlib.Path,
    ) -> None:
        with pytest.raises(ValueError):
            create_app(application.name, configuration=tmp_path, raise_on_none=True)
