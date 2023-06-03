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
    start: typing.Optional[typing.Sequence[str]] = None,
    end: typing.Optional[typing.Sequence[str]] = None,
    limit: typing.Optional[int] = 10,
) -> None:
    entries_result = use_cases.get_auditlog_entries(
        application,
        start=formatters.format_app_date(application, start),
        end=formatters.format_app_date(application, end),
        limit=limit,
        verbose_exc=verbose_exc,
        ascending_date=ascending_date,
    )

    if entries_result is not use_cases.UseCaseFailed:
        output.print(
            terminaltables.SingleTable(
                [
                    ["Date", "Is Failed", "Transaction Type", "Migration"],
                    *(formatters.format_auditlog_entry(entry) for entry in entries_result),
                ]
            ).table
        )


def show_version(application: applications.MigrationApp, verbose: bool) -> None:
    version_result = application.session.get_current_version()

    if version_result is not use_cases.UseCaseFailed:
        presentation = f"Current applied version is {version_result}"
        if verbose:
            all_applied_migrations_len = len(list(application.session.get_all_migration_models()))
            presentation += f" " + f"({version_result} of {all_applied_migrations_len})"

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
            presentation += f" " + (
                f"({application.session.get_current_version()}"
                f" "
                f"of {len(list(application.session.get_all_migration_models()))})"
            )

            output.print_heading(output.HEADING_LEVEL_ONE, output.TOOL_HEADING_NAME)
            output.print_info(presentation)
