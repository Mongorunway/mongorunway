from __future__ import annotations

import datetime
import sys
import traceback
import typing

from mongorunway import util
from mongorunway.application import output
from mongorunway.application import ux
from mongorunway.application.services import migration_service
from mongorunway.application.services import status_service

if typing.TYPE_CHECKING:
    from mongorunway.application import applications
    from mongorunway.application import config
    from mongorunway.application.ports import config_reader as config_reader_port
    from mongorunway.domain import migration_auditlog_entry as domain_auditlog_entry

_PLUS: typing.Final[str] = "+"
_MINUS: typing.Final[str] = "-"
_ALL: typing.Final[str] = "all"

_T = typing.TypeVar("_T")
_P = typing.ParamSpec("_P")

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


def upgrade(
    application: applications.MigrationApp,
    expression: str,
    verbose: bool,
    verbose_exc: bool,
) -> ExitCode:
    try:
        if expression == _PLUS:
            # +
            upgraded_count, executed_in = util.timeit_func(application.upgrade_once)
        elif expression == _ALL:
            # 'all'
            upgraded_count, executed_in = util.timeit_func(application.upgrade_all)
        elif expression.startswith(_PLUS):
            # +count
            upgraded_count, executed_in = util.timeit_func(
                application.upgrade_to,
                int(expression[1:]) + (application.session.get_current_version() or 0),
            )
        else:
            # digit
            upgraded_count, executed_in = util.timeit_func(
                application.upgrade_to,
                int(expression),
            )
    except BaseException as exc:
        _render_error(exc, verbose=verbose_exc)
        if type(exc) is ValueError:
            output.print_error(f"Invalid expression for upgrade: {expression!r}")

        return FAILURE

    _render_upgrade_results(verbose, upgraded_count, executed_in)

    return SUCCESS


def downgrade(
    application: applications.MigrationApp,
    expression: str,
    verbose: bool,
    verbose_exc: bool,
) -> ExitCode:
    try:
        if expression == _MINUS:
            # -
            downgraded_count, executed_in = util.timeit_func(application.downgrade_once)
        elif expression == _ALL:
            # 'all'
            downgraded_count, executed_in = util.timeit_func(application.downgrade_all)
        elif expression.startswith(_MINUS):
            # -count
            downgraded_count, executed_in = util.timeit_func(
                application.downgrade_to,
                int(expression) + (application.session.get_current_version() or 0),
            )
        else:
            # digit
            if not expression[0].isdigit():
                raise ValueError(f"The following expression cannot be applied: {expression!r}")

            downgraded_count, executed_in = util.timeit_func(
                application.downgrade_to,
                int(expression),
            )
    except BaseException as exc:
        _render_error(exc, verbose=verbose_exc)
        if type(exc) is ValueError:
            output.print_error(f"Invalid expression for downgrade: {expression!r}")

        return FAILURE

    _render_downgrade_results(verbose, downgraded_count, executed_in)

    return SUCCESS


def walk(
    application: applications.MigrationApp,
    expression: str,
    verbose: bool,
    verbose_exc: bool,
) -> ExitCode:
    try:
        if expression[0] not in {_PLUS, _MINUS}:
            raise ValueError(
                "This command can only go in positive or negative order. "
                "Therefore, the expression must begin with either the '+' or '-' character."
            )
    except BaseException as exc:
        _render_error(exc, verbose=verbose_exc)
        if type(exc) is ValueError:
            output.print_error(f"Invalid expression for walk: {expression!r}")

        return FAILURE

    if expression.startswith(_MINUS):
        return downgrade(application, expression, verbose, verbose_exc=verbose_exc)

    return upgrade(application, expression, verbose, verbose_exc=verbose_exc)


def create_migration_file(
    application: applications.MigrationApp,
    migration_filename: str,
    verbose_exc: bool,
    migration_version: typing.Optional[int] = None,
) -> ExitCode:
    if migration_version is None:
        output.print_info("Migration version is not specified, using auto-incrementation...")

    service = migration_service.MigrationService(application.session)
    try:
        service.create_migration_file_template(migration_filename, migration_version)
    except BaseException as exc:
        _render_error(exc, verbose=verbose_exc)
        return FAILURE

    return SUCCESS


def get_auditlog_entries(
    application: applications.MigrationApp,
    verbose_exc: bool,
    start: typing.Optional[datetime.datetime] = None,
    end: typing.Optional[datetime.datetime] = None,
    limit: typing.Optional[int] = None,
    ascending_date: bool = True,
) -> UseCaseFailedOr[typing.Sequence[domain_auditlog_entry.MigrationAuditlogEntry]]:
    try:
        history = application.session.history(
            start=start,
            end=end,
            limit=limit,
            ascending_date=ascending_date,
        )
    except BaseException as exc:
        _render_error(exc, verbose=verbose_exc)
        return UseCaseFailed

    return tuple(history)


def get_status(
    application: applications.MigrationApp,
    verbose_exc: bool,
    pushed_depth: int = -1,
) -> UseCaseFailedOr[typing.Tuple[bool, int]]:
    try:
        all_pushed_successfully = status_service.check_if_all_pushed_successfully(
            application=application,
            depth=pushed_depth,
        )
    except BaseException as exc:
        _render_error(exc, verbose=verbose_exc)
        return UseCaseFailed

    return all_pushed_successfully, pushed_depth


def get_pushed_version(
    application: applications.MigrationApp,
    verbose_exc: bool,
) -> UseCaseFailedOr[typing.Optional[int]]:
    try:
        version = application.session.get_current_version()
    except BaseException as exc:
        _render_error(exc, verbose=verbose_exc)
        return UseCaseFailed

    return version


def init(configuration: config.Config, verbose_exc: bool) -> ExitCode:
    try:
        ux.init_logging(configuration)
        ux.init_migration_directory(configuration)
        ux.init_migration_collection(configuration)
        ux.configure_migration_indexes(configuration)
    except BaseException as exc:
        _render_error(exc, verbose=verbose_exc)
        return FAILURE

    return SUCCESS


def read_configuration(
    config_filepath: str,
    *,
    app_name: str,
    verbose_exc: bool,
) -> UseCaseFailedOr[config.Config]:
    # This part of the infrastructure layer is used only in this use case and
    # is a necessary solution.
    from mongorunway.infrastructure.config_readers import IniFileConfigReader

    reader: typing.Optional[config_reader_port.ConfigReader] = None
    if config_filepath is None or config_filepath.endswith(".ini"):  # Default reader
        reader = IniFileConfigReader(app_name)

    if reader is None:
        output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
        output.print_error("Undefined configuration file type.")
        return UseCaseFailed

    try:
        configuration = reader.read_config(config_filepath)
    except BaseException as exc:
        _render_error(exc, verbose=verbose_exc)
        return UseCaseFailed

    return configuration


def _render_error(exc: BaseException, verbose: bool = False) -> None:
    output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
    output.print_warning(type(exc).__name__ + " : " + str(exc))

    if verbose:
        exc_info = traceback.format_exception(*sys.exc_info())
        output.print_error("\n".join(exc_info))


def _render_downgrade_results(verbose: bool, downgraded_count: int, executed_in: float) -> None:
    output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
    output.verbose_print(verbose, "Verbose mode enabled.")
    output.print_success(f"Successfully downgraded {downgraded_count} migration(s).")
    output.verbose_print(
        verbose,
        f"Downgraded {downgraded_count} migration(s) in {executed_in}s.",
    )


def _render_upgrade_results(verbose: bool, upgraded_count: int, executed_in: float) -> None:
    output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
    output.verbose_print(verbose, "Verbose mode enabled.")
    output.print_success(f"Successfully upgraded {upgraded_count} migration(s).")
    output.verbose_print(verbose, f"Upgraded {upgraded_count} migration(s) in {executed_in}s.")
