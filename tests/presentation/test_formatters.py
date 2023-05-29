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

import datetime
import types
import typing

import bson
import pytest

from mongorunway.presentation.formatters import format_auditlog_entry
from mongorunway.presentation.formatters import format_app_date
from mongorunway.domain import migration_auditlog_entry as domain_auditlog_entry
from mongorunway.domain import migration as domain_migration

if typing.TYPE_CHECKING:
    from mongorunway.application import applications


@pytest.mark.parametrize(
    "date_parts, expected_type",
    [
        (["2022-01-01", "12:34:56"], datetime.datetime),
        (None, types.NoneType)
    ]
)
def test_format_app_date(
    application: applications.MigrationApp,
    date_parts: typing.Optional[typing.Sequence[str]],
    expected_type: typing.Type[typing.Any],
) -> None:
    result = format_app_date(application, date_parts)
    assert isinstance(result, expected_type)


def test_format_auditlog_entry(migration: domain_migration.Migration) -> None:
    entry = domain_auditlog_entry.MigrationAuditlogEntry(
        session_id=bson.Binary(b"123"),
        transaction_name="Transaction",
        migration_read_model=domain_migration.MigrationReadModel.from_migration(migration),
        date_fmt="%Y-%m-%d %H:%M:%S",
        date=datetime.datetime(2022, 1, 1, 12, 34, 56),
        exc_name=None,
        exc_message=None
    )

    expected_result = [
        "2022-01-01 12:34:56",
        "False",
        "Transaction",
        f"Name: {migration.name}\n"
        f"Version: {migration.version}\n"
        f"Is applied: {migration.is_applied}\n"
    ]

    result = format_auditlog_entry(entry)
    assert result == expected_result


def test_format_auditlog_entry_with_error(migration: domain_migration.Migration) -> None:
    entry = domain_auditlog_entry.MigrationAuditlogEntry(
        session_id=bson.Binary(b"123"),
        transaction_name="Transaction",
        migration_read_model=domain_migration.MigrationReadModel.from_migration(migration),
        date_fmt="%Y-%m-%d %H:%M:%S",
        date=datetime.datetime(2022, 1, 1, 12, 34, 56),
        exc_name="ValueError",
        exc_message="Something went wrong"
    )

    expected_result = [
        "2022-01-01 12:34:56",
        "Error: ValueError\nMessage: Something went wrong",
        "Transaction",
        f"Name: {migration.name}\n"
        f"Version: {migration.version}\n"
        f"Is applied: {migration.is_applied}\n"
    ]

    result = format_auditlog_entry(entry)
    assert result == expected_result
