from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from mongorunway.domain import migration_auditlog_entry as domain_auditlog_entry


def one_of_all(one: typing.Any, all_: typing.Any, *, concat_to: str) -> str:
    return " ".join((concat_to, f"({one} of {all_})"))


def auditlog_entry_fields(
    entry: domain_auditlog_entry.MigrationAuditlogEntry, /
) -> typing.Sequence[str]:
    migration = entry.migration
    return [
        entry.date.strftime("%Y-%m-%d %H:%M:%S"),
        "False" if entry.is_failed() else f"Error: {entry.exc_name}\nMessage: {entry.exc_message}",
        entry.transaction_name,
        f"Name: {migration.name}\n"
        f"Version: {migration.version}\n"
        f"Is applied: {migration.is_applied}\n",
    ]
