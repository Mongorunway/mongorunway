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
"""A module that provides high-level tools for public use."""
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
    r"""Creates a migration application.

    Creates a migration application based on the provided parameters.
    Uses a use case to initialize the application configuration.

    Parameters
    ----------
    name : str
        The name of the application for which the creation options will
        be taken from the configuration file. The application name should
        match the application name in the configuration file.
    configuration : typing.Optional[typing.Union[os.PathLike[str], str, pathlib.Path, config.Config]]
        The path to the configuration file or the configuration object
        required for initializing the application.
    raise_on_none : bool, optional
        By default, the use-cases return None and do not raise exceptions.
        If `raise_on_none` is True, an exception will be raised on a failed
        attempt to initialize the application.
    verbose_exc : bool, optional
        In case of an exception being raised on a failed attempt to initialize
        the application, the exception information will be more detailed if
        `verbose_exc` is True.

    Raises
    ------
    RuntimeError
        If `raise_on_none` is True and the initialization of the application fails,
        this exception will be raised.

    Returns
    -------
    typing.Union[MigrationApp, typing.Optional[MigrationApp]]
        If `raise_on_none` is True, an application object is guaranteed to be
        returned or an exception is raised. Otherwise, if the application
        initialization fails, None is returned.
    """

    if not isinstance(configuration, config.Config) or configuration is None:
        configuration = use_cases.read_configuration(
            config_filepath=str(configuration) if configuration is not None else configuration,
            app_name=name,
            verbose_exc=verbose_exc,
        )

    if configuration is not use_cases.UseCaseFailed:
        return applications.MigrationAppImpl(configuration=configuration)

    if raise_on_none:
        raise RuntimeError(f"Creation of {name!r} application is failed.")

    return None


def raise_if_migration_version_mismatch(
    application: applications.MigrationApp,
    expected_version: typing.Union[int, typing.Callable[[], int]],
) -> None:
    r"""Raises an error if the versions do not match.

    Raises an error if the provided version or version getter does not
    match the version of the given migration application. The expected
    version or the return value of the expected version getter should
    be an instance of the `int` class. Otherwise, the comparison operation
    may behave unpredictably.

    Parameters
    ----------
    application : applications.MigrationApp
        The migration application whose version you want to check.
    expected_version : typing.Union[int, typing.Callable[[], int]]
        The expected version of the current migration application.
        The expected version or the return value of the expected version
        getter should be an instance of the `int` class. Otherwise, the
        comparison operation may behave unpredictably.

    Raises
    ------
    ValueError
        Raises an error if the provided version or version getter does
        not match the version of the given migration application.
    """

    if callable(expected_version):
        expected_version = expected_version()

    if (current_version := (application.session.get_current_version() or 0)) != expected_version:
        raise ValueError(
            f"Migration version mismatch."
            " "
            f"Actual: {current_version!r}, but {expected_version!r} expected."
        )

    return None


def migration(process_func: types.FunctionType, /) -> domain_migration.MigrationProcess:
    r"""Wraps a function in a migration process.

    Wraps a function in a migration process. The function should return
    either a ready-to-use migration process object or a sequence containing
    implementations of migration command interfaces. Otherwise, an exception
    will be raised (see the `Raises` section).

    !!! note
        **__name__**: If the provided object does not have the `__name__`
        attribute, the default name `UNDEFINED_PROCESS` will be set, which is
        used for debugging and logging migration processes.

        **__globals__**: If the provided object does not have the `__globals__`
        attribute, an `AttributeError` will be raised (see the `Raises`
        section).

    Parameters
    ----------
    process_func : types.FunctionType
        The function that returns either a ready-to-use migration process object
        or a sequence containing implementations of migration command interfaces.

    Returns
    -------
    domain_migration.MigrationProcess
        A migration process object that contains information about the migration
        version, process name, and set of migration commands. If the function
        returns an already created migration process, no new objects will be
        created.

    Raises
    ------
    ValueError
        If the function did not return an instance of the migration process
        class and the return value is not an instance of collections.abc.Sequence.
    AttributeError
        If the function did not return an instance of the migration process
        class and the module where the function is implemented does not contain
        the global value `version`.
    """

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

        raise AttributeError(f"Migration module {func_file!r} should have 'version' variable.")

    return domain_migration.MigrationProcess(
        func_callback,
        migration_version=version,
        name=getattr(process_func, "__name__", "UNDEFINED_PROCESS"),
    )


def migration_with_rule(
    rule: domain_rule.MigrationBusinessRule, /
) -> typing.Callable[[_ProcessT], _ProcessT]:
    r"""Adds a rule to the migration process.

    Returns the provided migration process object with the added rule.

    Parameters
    ----------
    rule : domain_rule.MigrationBusinessRule
        The rule to add to the migration process.

    Raises
    ------
    ValueError
        If the value passed to the decorator is not an instance of the migration
        process class.
    """

    if not isinstance(rule, domain_rule.MigrationBusinessRule):
        raise ValueError(f"Rule must be instance of {domain_rule.MigrationBusinessRule!r}.")

    def decorator(process: _ProcessT) -> _ProcessT:
        process.add_rule(rule)
        return process

    return decorator
