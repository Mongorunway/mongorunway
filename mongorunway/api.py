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
    "create_app",
    "raise_if_migration_version_mismatch",
    "migration",
    "migration_with_rule",
)

import collections.abc
import os
import pathlib
import types
import typing

from mongorunway.application import applications
from mongorunway.application import config
from mongorunway.application import use_cases
from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_business_rule as domain_rule

if typing.TYPE_CHECKING:
    from mongorunway.application.applications import MigrationApp

_ProcessT = typing.TypeVar("_ProcessT", bound=domain_migration.MigrationProcess)


@typing.overload
def create_app(
    name: str,
    configuration: typing.Optional[
        typing.Union[os.PathLike[str], str, pathlib.Path, config.Config]
    ] = None,
    *,
    raise_on_none: typing.Literal[True] = True,
    verbose_exc: bool = False,
) -> MigrationApp:
    ...


@typing.overload
def create_app(
    name: str,
    configuration: typing.Optional[
        typing.Union[os.PathLike[str], str, pathlib.Path, config.Config]
    ] = None,
    *,
    raise_on_none: typing.Literal[False] = False,
    verbose_exc: bool = False,
) -> typing.Optional[MigrationApp]:
    ...


def create_app(
    name: str,
    configuration: typing.Optional[
        typing.Union[os.PathLike[str], str, pathlib.Path, config.Config]
    ] = None,
    *,
    raise_on_none: bool = False,
    verbose_exc: bool = False,
) -> typing.Union[MigrationApp, typing.Optional[MigrationApp]]:
    if not isinstance(configuration, config.Config) or configuration is None:
        configuration = use_cases.read_configuration(
            config_filepath=str(configuration) if configuration is not None else configuration,
            app_name=name,
            verbose_exc=verbose_exc,
        )

    if configuration is not use_cases.UseCaseFailed:
        return applications.MigrationAppImpl(configuration=configuration)

    if raise_on_none:
        raise ValueError(f"Creation of {name!r} application is failed.")

    return None


def raise_if_migration_version_mismatch(
    app: applications.MigrationApp,
    expected_version: typing.Union[int, typing.Callable[[], int]],
) -> None:
    if callable(expected_version):
        expected_version = expected_version()

    if (current_version := (app.session.get_current_version() or 0)) != expected_version:
        raise ValueError(
            f"Migration version mismatch."
            " "
            f"Actual: {current_version!r}, but {expected_version!r} expected."
        )


def migration(process_func: types.FunctionType, /) -> domain_migration.MigrationProcess:
    func_callback = process_func()
    if isinstance(func_callback, domain_migration.MigrationProcess):
        return func_callback

    if not isinstance(func_callback, collections.abc.Sequence):
        raise ValueError(
            f"Migration process func {process_func!r} must return sequence of commands."
        )

    version = getattr(process_func, "__globals__", {}).get("version", None)
    if version is None:
        func_file = ""
        if hasattr(process_func, "__code__"):
            func_file = process_func.__code__.co_filename

        raise ValueError(f"Migration module {func_file!r} should have 'version' variable.")

    return domain_migration.MigrationProcess(
        func_callback,
        migration_version=version,
        name=getattr(process_func, "__name__", "UNDEFINED_PROCESS"),
    )


def migration_with_rule(
    rule: domain_rule.MigrationBusinessRule, /
) -> typing.Callable[[_ProcessT], _ProcessT]:
    if not isinstance(rule, domain_rule.MigrationBusinessRule):
        raise ValueError(f"Rule must be instance of {domain_rule.MigrationBusinessRule!r}.")

    def decorator(process: _ProcessT) -> _ProcessT:
        process.add_rule(rule)
        return process

    return decorator
