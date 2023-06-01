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
)

import datetime
import functools
import sys
import traceback
import typing

from mongorunway import util
from mongorunway.application import output
from mongorunway.application import ux
from mongorunway.application.ports import config_reader as config_reader_port
from mongorunway.application.services import migration_service
from mongorunway.application.services import status_service

if typing.TYPE_CHECKING:
    from mongorunway.application import applications
    from mongorunway.application import config
    from mongorunway.domain import migration_auditlog_entry as domain_auditlog_entry

_T = typing.TypeVar("_T")
_P = typing.ParamSpec("_P")

PLUS: typing.Final[str] = "+"
MINUS: typing.Final[str] = "-"
ALL: typing.Final[str] = "all"

ExitCode: typing.TypeAlias = int

SUCCESS: typing.Final[ExitCode] = 0

FAILURE: typing.Final[ExitCode] = 1

UseCaseFailed: typing.Any = object()
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
            except BaseException as exc:
                render_error(
                    exc,
                    verbose=kwargs["verbose_exc"] if has_verbose_exc else False,
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
            except BaseException as exc:
                render_error(
                    exc,
                    verbose=kwargs["verbose_exc"] if has_verbose_exc else False,
                )
                return UseCaseFailed

            return callback

        return wrapper

    return decorator


@usecase(has_verbose_exc=True)
def downgrade(
    application: applications.MigrationApp,
    expression: str,
    verbose: bool,
    verbose_exc: bool,
) -> ExitCode:
    func, args = None, ()
    if expression.isdigit():
        func, args = application.downgrade_to, (int(expression),)
    elif len(expression) > 1 and expression.startswith(MINUS):
        func, args = application.downgrade_to, (
            int(expression) + application.session.get_current_version() or 0,
        )
    elif expression == MINUS:
        func = application.downgrade_once
    elif expression == ALL:
        func = application.downgrade_all

    if func is None:
        raise ValueError(f"The following expression cannot be applied: {expression!r}")

    render_downgrade_results(
        verbose,
        *util.timeit_func(func, *args),
    )

    return SUCCESS


@usecase(has_verbose_exc=True)
def upgrade(
    application: applications.MigrationApp,
    expression: str,
    verbose: bool,
    verbose_exc: bool,
) -> ExitCode:
    func, args = None, ()
    if expression.isdigit():
        func, args = application.upgrade_to, (int(expression),)
    elif expression.startswith(PLUS):
        func, args = application.upgrade_to, (
            int(expression[1:]) + (application.session.get_current_version() or 0),
        )
    elif expression == PLUS:
        func = application.upgrade_once
    elif expression == ALL:
        func = application.upgrade_all

    if func is None:
        raise ValueError(f"The following expression cannot be applied: {expression!r}")

    render_upgrade_results(
        verbose,
        *util.timeit_func(func, *args),
    )

    return SUCCESS


@usecase(has_verbose_exc=True)
def walk(
    application: applications.MigrationApp,
    expression: str,
    verbose: bool,
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
            verbose=verbose,
            verbose_exc=verbose_exc,
        )

    return upgrade(
        application=application,
        expression=expression,
        verbose=verbose,
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
    if config_filepath is None or config_filepath.endswith(".yaml"):  # Default reader
        reader = util.import_obj(
            "mongorunway.infrastructure.config_readers.YamlConfigReader",
            cast=config_reader_port.ConfigReader,
        ).from_application_name(app_name)

    if reader is None:
        output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
        output.print_error("Undefined configuration file type.")
        return UseCaseFailed

    configuration = reader.read_config(config_filepath)

    return configuration


def render_error(exc: BaseException, verbose: bool = False) -> None:
    output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
    output.print_warning(type(exc).__name__ + " : " + str(exc))

    if verbose:
        exc_info = traceback.format_exception(*sys.exc_info())
        output.print_error("\n".join(exc_info))


def render_downgrade_results(verbose: bool, downgraded_count: int, executed_in: float) -> None:
    output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
    output.verbose_print(verbose, "Verbose mode enabled.")
    output.print_success(f"Successfully downgraded {downgraded_count} migration(s).")
    output.verbose_print(
        verbose,
        f"Downgraded {downgraded_count} migration(s) in {executed_in}s.",
    )


def render_upgrade_results(verbose: bool, upgraded_count: int, executed_in: float) -> None:
    output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
    output.verbose_print(verbose, "Verbose mode enabled.")
    output.print_success(f"Successfully upgraded {upgraded_count} migration(s).")
    output.verbose_print(verbose, f"Upgraded {upgraded_count} migration(s) in {executed_in}s.")
