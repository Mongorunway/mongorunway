from __future__ import annotations

__all__: typing.Sequence[str] = (
    "format_auditlog_entry",
    "format_app_date",
)

import datetime
import typing

if typing.TYPE_CHECKING:
    from mongorunway.domain import migration_auditlog_entry as domain_auditlog_entry
    from mongorunway.application import applications


def format_app_date(
    application: applications.MigrationApp,
    date_parts: typing.Optional[typing.Sequence[str]],
) -> typing.Optional[datetime.datetime]:
    if date_parts is None:
        return None

    return datetime.datetime.strptime(
        " ".join(date_parts),
        application.session.session_config.application.app_date_format,
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
