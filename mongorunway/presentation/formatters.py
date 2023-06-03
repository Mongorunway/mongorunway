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
    "format_auditlog_entry",
    "format_app_date",
)

import datetime
import typing

if typing.TYPE_CHECKING:
    from mongorunway.application import applications
    from mongorunway.domain import migration_auditlog_entry as domain_auditlog_entry


def format_app_date(
    application: applications.MigrationApp,
    date_parts: typing.Optional[typing.Sequence[str]],
) -> typing.Optional[datetime.datetime]:
    if date_parts is None:
        return None

    return datetime.datetime.strptime(
        " ".join(date_parts),
        application.session.session_date_format,
    )


def format_auditlog_entry(
    entry: domain_auditlog_entry.MigrationAuditlogEntry, /
) -> typing.Sequence[str]:
    migration = entry.migration_read_model

    failed_msg = "False"
    if entry.is_failed():
        failed_msg = f"Error: {entry.exc_name}\nMessage: {entry.exc_message}"

    return [
        entry.format_date(),
        failed_msg,
        entry.transaction_name,
        f"Name: {migration.name}\n"
        f"Version: {migration.version}\n"
        f"Is applied: {migration.is_applied}\n",
    ]
