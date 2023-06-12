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
    "ALL",
    "ExitCode",
    "FAILURE",
    "MINUS",
    "PLUS",
    "SUCCESS",
    "UseCaseFailed",
    "UseCaseFailedOr",
    "create_migration_file",
    "downgrade",
    "get_auditlog_entries",
    "get_pushed_version",
    "get_status",
    "read_configuration",
    "render_downgrade_results",
    "render_error",
    "render_upgrade_results",
    "upgrade",
    "usecase",
    "walk",
    "refresh",
    "safe_remove_migration",
    "safe_remove_all_migrations",
    "check_files",
    "refresh_checksums",
)

import datetime
import functools
import os
import sys
import traceback
import typing

import typing_extensions

from mongorunway import util
from mongorunway.application import output
from mongorunway.application import ux
from mongorunway.application.ports import config_reader as config_reader_port
from mongorunway.application.services import migration_service
from mongorunway.application.services import status_service
from mongorunway.domain import migration_exception as domain_exception

if typing.TYPE_CHECKING:
    from mongorunway.application import applications
    from mongorunway.application import config
    from mongorunway.domain import migration_auditlog_entry as domain_auditlog_entry

_T = typing.TypeVar("_T")
try:
    _P = typing.ParamSpec("_P")
except AttributeError:
    _P = typing_extensions.ParamSpec("_P")

PLUS: typing.Final[str] = "+"
MINUS: typing.Final[str] = "-"
ALL: typing.Final[str] = "all"

ExitCode: typing.TypeAlias = int

SUCCESS: typing.Final[ExitCode] = 0

FAILURE: typing.Final[ExitCode] = 1

UseCaseFailed: typing.TypeAlias = object()
r"""Use case callback sentinel.

Some use cases that are designed to retrieve specific data may, by design, 
return None. However, since errors at the use case level are not raised but 
handled and logged to the console, it has been decided to make it a general 
rule to return the UseCaseFailed sentinel in case of a failed use case.

Notes
-----
It is important to differentiate between ExitCode and this sentinel: 'ExitCode' 
is returned by commands that are meant to perform a specific action without being 
tied to a particular result. On the other hand, as mentioned earlier, UseCaseFailed 
is intended for the opposite scenario: for commands that are meant  to search and 
compute data and are expected to return a result.

See Also
--------
ExitCode
"""

if sys.version_info < (3, 11):
    UseCaseFailed: typing.TypeAlias = typing.Any

UseCaseFailedOr = typing.Union[_T, UseCaseFailed]


def usecase(
    *,
    has_verbose_exc: bool,
) -> typing.Callable[[typing.Callable[_P, _T]], typing.Callable[_P, ExitCode]]:
    def decorator(func: typing.Callable[_P, _T]) -> typing.Callable[_P, ExitCode]:
        @functools.wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> ExitCode:
            try:
                func(*args, **kwargs)
            except Exception as exc:
                render_error(
                    exc,
                    verbose_exc=typing.cast(
                        bool,
                        kwargs["verbose_exc"] if has_verbose_exc else False,
                    ),
                )
                return FAILURE

            return SUCCESS

        return wrapper

    return decorator


def query_usecase(
    *,
    has_verbose_exc: bool,
) -> typing.Callable[[typing.Callable[_P, _T]], typing.Callable[_P, UseCaseFailedOr[_T]]]:
    def decorator(func: typing.Callable[_P, _T]) -> typing.Callable[_P, UseCaseFailedOr[_T]]:
        @functools.wraps(func)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> UseCaseFailedOr[_T]:
            try:
                callback = func(*args, **kwargs)
            except Exception as exc:
                render_error(
                    exc,
                    verbose_exc=typing.cast(
                        bool,
                        kwargs["verbose_exc"] if has_verbose_exc else False,
                    ),
                )
                return UseCaseFailed

            return callback

        return wrapper

    return decorator


@usecase(has_verbose_exc=True)
def downgrade(
    application: applications.MigrationApp,
    expression: str,
    verbose_exc: bool,
) -> ExitCode:
    func: typing.Optional[typing.Callable[..., ExitCode]] = None
    args: typing.Tuple[typing.Any, ...] = ()

    if expression.isdigit():
        func, args = application.downgrade_to, (int(expression),)
    elif expression == MINUS:
        func = application.downgrade_once
    elif len(expression) > 1 and expression.startswith(MINUS):
        func, args = application.downgrade_to, (
            int(expression) + (application.session.get_current_version() or 0),
        )
    elif expression == ALL:
        func = application.downgrade_all

    if func is None:
        raise ValueError(f"The following expression cannot be applied: {expression!r}")

    render_downgrade_results(*util.timeit_func(func, *args))

    return SUCCESS


@usecase(has_verbose_exc=True)
def upgrade(
    application: applications.MigrationApp,
    expression: str,
    verbose_exc: bool,
) -> ExitCode:
    func: typing.Optional[typing.Callable[..., ExitCode]] = None
    args: typing.Tuple[typing.Any, ...] = ()

    if expression.isdigit():
        func, args = application.upgrade_to, (int(expression),)
    elif expression == PLUS:
        func = application.upgrade_once
    elif expression.startswith(PLUS):
        func, args = application.upgrade_to, (
            int(expression[1:]) + (application.session.get_current_version() or 0),
        )
    elif expression == ALL:
        func = application.upgrade_all

    if func is None:
        raise ValueError(f"The following expression cannot be applied: {expression!r}")

    render_upgrade_results(*util.timeit_func(func, *args))

    return SUCCESS


@usecase(has_verbose_exc=True)
def walk(
    application: applications.MigrationApp,
    expression: str,
    verbose_exc: bool,
) -> ExitCode:
    if expression[0] not in {PLUS, MINUS}:
        raise ValueError(
            "This command can only go in positive or negative order. "
            "Therefore, the expression must begin with either the '+' "
            "or '-' character."
        )

    if expression.startswith(MINUS):
        return downgrade(
            application=application,
            expression=expression,
            verbose_exc=verbose_exc,
        )

    return upgrade(
        application=application,
        expression=expression,
        verbose_exc=verbose_exc,
    )


@usecase(has_verbose_exc=True)
def create_migration_file(
    application: applications.MigrationApp,
    migration_filename: str,
    verbose_exc: bool,
    migration_version: typing.Optional[int] = None,
) -> ExitCode:
    if migration_version is None:
        output.print_info("Migration version is not specified, using auto-incrementation...")

    service = migration_service.MigrationService(application.session)
    service.create_migration_file_template(migration_filename, migration_version)

    return SUCCESS


@usecase(has_verbose_exc=True)
def safe_remove_migration(
    application: applications.MigrationApp,
    migration_version: int,
    verbose_exc: bool,
) -> ExitCode:
    migration = application.session.get_migration_model_by_version(migration_version)
    output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)

    if migration is None:
        output.print_error(f"Migration with version '{migration_version}' is not found.")
        return FAILURE

    latest, *_ = application.session.get_all_migration_models(ascending_id=False)
    if migration.version != latest.version:
        output.print_error(
            f"Removing migrations must be sequential."
            f" "
            f"The currently available version for deletion is"
            f" "
            f"'{latest.version}'"
        )
        return FAILURE

    application.session.remove_migration(migration_version)
    output.print_success(
        f"Migration with version {migration_version} has been successfully deleted."
    )

    directory = application.session.session_scripts_dir
    if os.path.exists(fp := (directory + "\\" + migration.name + ".py")):
        os.remove(fp)

    return SUCCESS


@usecase(has_verbose_exc=True)
def check_files(
    application: applications.MigrationApp,
    raise_exc: bool,
    verbose_exc: bool,
) -> ExitCode:
    service = migration_service.MigrationService(application.session)
    failed_migrations = []
    output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)

    for migration in application.session.get_all_migration_models():
        current_migration_state = service.get_migration(migration.name, migration.version)
        if current_migration_state.checksum != migration.checksum:
            failed_migrations.append(current_migration_state)

    if failed_migrations:
        output.print_error(
            f"'{', '.join(m.name for m in failed_migrations)}' migration file(s) are changed."
        )
        if raise_exc:
            raise domain_exception.MigrationFilesChangedError(*[m.name for m in failed_migrations])

        return FAILURE

    output.print_success("All files remain in their previous state.")
    return SUCCESS


@usecase(has_verbose_exc=True)
def refresh_checksums(application: applications.MigrationApp, verbose_exc: bool) -> ExitCode:
    service = migration_service.MigrationService(application.session)
    modified_files = []

    for migration in application.session.get_all_migration_models():
        current_migration_state = service.get_migration(migration.name, migration.version)

        if current_migration_state.checksum != migration.checksum:
            application.session.remove_migration(migration.version)
            application.session.append_migration(current_migration_state)

            modified_files.append(current_migration_state.name)

    if modified_files:
        output.print_success(
            f"'{', '.join(modified_files)}' files have been modified, and their "
            f"checksums have been successfully updated."
        )
    else:
        output.print_info("All files remain in their previous state.")

    return SUCCESS


@usecase(has_verbose_exc=True)
def safe_remove_all_migrations(
    application: applications.MigrationApp,
    verbose_exc: bool,
) -> ExitCode:
    migrations = application.session.get_all_migration_models()

    output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
    if not migrations:
        output.print_error("There is no migrations.")
        return FAILURE

    for migration in migrations:
        application.session.remove_migration(migration.version)

    directory = application.session.session_scripts_dir
    for file_name in os.listdir(directory):
        if file_name.startswith("_") or not file_name.endswith(".py"):
            continue

        file_path = os.path.join(directory, file_name)
        os.remove(file_path)

    output.print_success(f"Successfully deleted {len(migrations)} migration(s).")
    return SUCCESS


@usecase(has_verbose_exc=True)
def init(
    application: applications.MigrationApp,
    verbose_exc: bool,
    init_scripts_dir: bool,
    init_collection: bool,
    init_collection_indexes: bool,
    init_collection_schema_validation: bool,
) -> ExitCode:
    if init_scripts_dir:
        ux.configure_migration_directory(application.session.session_scripts_dir)
    if init_collection:
        ux.configure_migration_collection(
            application.session.session_database,
            use_schema_validation=init_collection_schema_validation,
        )
    if init_collection_indexes:
        ux.configure_migration_indexes(application.session.session_database.migrations)

    return SUCCESS


@usecase(has_verbose_exc=True)
def refresh(
    application: applications.MigrationApp,
    verbose_exc: bool,
) -> ExitCode:
    synced_names = ux.sync_scripts_with_repository(application)
    output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
    if synced_names:
        output.print_success(f"'{', '.join(synced_names)}' migration(s) was successfully synced.")
    else:
        output.print_error("There is no unsynced migrations.")

    return SUCCESS


@query_usecase(has_verbose_exc=True)
def get_auditlog_entries(
    application: applications.MigrationApp,
    verbose_exc: bool,
    start: typing.Optional[datetime.datetime] = None,
    end: typing.Optional[datetime.datetime] = None,
    limit: typing.Optional[int] = None,
    ascending_date: bool = True,
) -> UseCaseFailedOr[typing.Sequence[domain_auditlog_entry.MigrationAuditlogEntry]]:
    history = application.session.history(
        start=start,
        end=end,
        limit=limit,
        ascending_date=ascending_date,
    )

    return tuple(history)


@query_usecase(has_verbose_exc=True)
def get_status(
    application: applications.MigrationApp,
    verbose_exc: bool,
    pushed_depth: int = -1,
) -> UseCaseFailedOr[typing.Tuple[bool, int]]:
    all_pushed_successfully = status_service.check_if_all_pushed_successfully(
        application=application,
        depth=pushed_depth,
    )

    return all_pushed_successfully, pushed_depth


@query_usecase(has_verbose_exc=True)
def get_pushed_version(
    application: applications.MigrationApp,
    verbose_exc: bool,
) -> UseCaseFailedOr[typing.Optional[int]]:
    version = application.session.get_current_version()
    return version


@query_usecase(has_verbose_exc=True)
def read_configuration(
    config_filepath: typing.Optional[str],
    *,
    app_name: str,
    verbose_exc: bool,
) -> UseCaseFailedOr[config.Config]:
    reader: typing.Optional[config_reader_port.ConfigReader] = None
    if (
        config_filepath is None
        or config_filepath.endswith(".yaml")
        or config_filepath.endswith(".yml")
    ):  # Default reader
        reader = util.import_obj(
            "mongorunway.infrastructure.config_readers.YamlConfigReader",
            cast=config_reader_port.ConfigReader,
        ).from_application_name(app_name)

    if reader is None:
        output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
        output.print_error("Undefined configuration file type.")
        return UseCaseFailed

    configuration = reader.read_config(config_filepath)
    if configuration is None:
        output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
        output.print_error(f"Cannot find any configuration files in {config_filepath} directory.")
        return UseCaseFailed

    return configuration


def render_error(exc: Exception, verbose_exc: bool = False) -> None:
    output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
    output.print_warning(type(exc).__name__ + " : " + str(exc))

    if verbose_exc:
        exc_info = traceback.format_exception(*sys.exc_info())
        output.print_error("\n".join(exc_info))


def render_downgrade_results(downgraded_count: int, executed_in: float) -> None:
    output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
    output.print_success(f"Successfully downgraded {downgraded_count} migration(s).")
    output.print_info(
        f"Downgraded {downgraded_count} migration(s) in {executed_in}s.",
    )


def render_upgrade_results(upgraded_count: int, executed_in: float) -> None:
    output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
    output.print_success(f"Successfully upgraded {upgraded_count} migration(s).")
    output.print_info(f"Upgraded {upgraded_count} migration(s) in {executed_in}s.")
