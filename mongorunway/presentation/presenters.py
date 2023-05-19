from __future__ import annotations

import datetime
import typing

import terminaltables  # type: ignore[import]

from mongorunway.application import output
from mongorunway.application import use_cases
from mongorunway.presentation import formatters

if typing.TYPE_CHECKING:
    from mongorunway.application import applications


def show_auditlog_entries(
    application: applications.MigrationApp,
    verbose_exc: bool,
    ascending_date: bool,
    start: typing.Optional[datetime.datetime] = None,
    end: typing.Optional[datetime.datetime] = None,
    limit: typing.Optional[int] = 10,
) -> None:
    entries_result = use_cases.get_auditlog_entries(
        application,
        start=start,
        end=end,
        limit=limit,
        verbose_exc=verbose_exc,
        ascending_date=ascending_date,
    )

    if entries_result is not use_cases.UseCaseFailed:
        output.print(
            terminaltables.SingleTable(
                [
                    ["Date", "Is Failed", "Transaction Type", "Migration"],
                    *(formatters.auditlog_entry_fields(entry) for entry in entries_result),
                ]
            ).table
        )


def show_version(application: applications.MigrationApp, verbose: bool) -> None:
    version_result = application.session.get_current_version()

    if version_result is not use_cases.UseCaseFailed:
        presentation = f"Current applied version is {version_result}"
        if verbose:
            all_applied_migrations_len = len(application.session.get_all_migration_models())
            presentation = formatters.one_of_all(
                version_result,
                all_applied_migrations_len,
                concat_to=presentation,
            )

        output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
        output.print_success(presentation)


def show_status(
    application: applications.MigrationApp,
    verbose: bool,
    verbose_exc: bool,
    pushed_depth: int = -1,
) -> None:
    status_result = use_cases.get_status(
        application=application,
        verbose_exc=verbose_exc,
        pushed_depth=pushed_depth,
    )

    if status_result is not use_cases.UseCaseFailed:
        all_pushed_successfully, pushed_depth = status_result
        if all_pushed_successfully:
            presentation = f"All migrations applied successfully in depth {pushed_depth!r}"
        else:
            presentation = f"Applying failed in depth {pushed_depth!r}"

        if verbose:
            presentation = formatters.one_of_all(
                application.session.get_current_version(),
                len(application.session.get_all_migration_models()),
                concat_to=presentation,
            )
            output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
            output.print_info(presentation)
