from __future__ import annotations

import logging
import typing

from mongorunway.application.services import migration_service
from mongorunway.domain import migration_event as domain_event
from mongorunway.domain import migration_exception as domain_exception

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("root.event_handlers")


def sync_scripts_with_queues(event: domain_event.ApplicationEvent) -> None:
    service = migration_service.MigrationService(event.application.session)
    for migration in service.get_migrations():
        if not event.application.session.has_migration(migration):
            event.application.session.append_migration(migration)

            _LOGGER.info(
                "%s: migration '%s' with version %s was synced"
                " "
                "and successfully append to pending.",
                sync_scripts_with_queues.__name__,
                migration.name,
                migration.version,
            )


def recalculate_migrations_checksum(event: domain_event.ApplicationEvent) -> None:
    service = migration_service.MigrationService(event.application.session)

    for migration in event.application.session.get_all_migration_models():
        current_migration_state = service.get_migration(migration.name)

        if current_migration_state.checksum != migration.checksum:
            event.application.session.remove_migration(migration.version)
            event.application.session.append_migration(current_migration_state)

            _LOGGER.info(
                "%s: migration file '%s' with version %s is changed, checksum successfully"
                " "
                "recalculated (%s) -> (%s).",
                recalculate_migrations_checksum.__name__,
                migration.name,
                migration.version,
                migration.checksum,
                current_migration_state.checksum,
            )


def raise_if_migrations_checksum_mismatch(event: domain_event.ApplicationEvent) -> None:
    service = migration_service.MigrationService(event.application.session)

    for migration in event.application.session.get_all_migration_models():
        current_migration_state = service.get_migration(migration.name)
        if current_migration_state.checksum != migration.checksum:
            _LOGGER.error(
                "%s: migration file '%s' with version %s is changed, raising...",
                raise_if_migrations_checksum_mismatch.__name__,
                migration.name,
                migration.version,
            )
            raise domain_exception.MigrationFileChangedError(
                migration_name=migration.name,
                migration_version=migration.version,
            )
