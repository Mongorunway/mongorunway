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

import os
import typing

import pytest

from mongorunway.application.services import migration_service
from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_event as domain_event
from mongorunway.domain import migration_exception as domain_exception
from mongorunway.infrastructure.event_handlers import raise_if_migrations_checksum_mismatch
from mongorunway.infrastructure.event_handlers import recalculate_migrations_checksum
from mongorunway.infrastructure.event_handlers import sync_scripts_with_queues
from tests import tools

if typing.TYPE_CHECKING:
    from mongorunway.application import applications
    from mongorunway.application import config


def test_sync_scripts_with_queues(
    migration: domain_migration.Migration,
    application: applications.MigrationApp,
) -> None:
    service = migration_service.MigrationService(application.session)

    assert len(service.get_migrations()) == 0
    service.create_migration_file_template(migration.name, migration.version)
    assert len(service.get_migrations()) == 1

    assert len(list(application.session.get_all_migration_models())) == 0
    sync_scripts_with_queues(domain_event.ApplicationEvent(application=application))
    assert len(list(application.session.get_all_migration_models())) == 1


def test_recalculate_migrations_checksum(
    migration: domain_migration.Migration,
    configuration: config.Config,
    application: applications.MigrationApp,
) -> None:
    service = migration_service.MigrationService(application.session)
    service.create_migration_file_template(migration.name, migration.version)
    migration = service.get_migration(migration.name, migration.version)

    application.session.append_migration(migration)

    file_state = service.get_migration(migration.name, migration.version)
    db_state = application.session.get_migration_model_by_version(migration.version)

    assert file_state.checksum == db_state.checksum

    filepath = tools.get_migration_file_path(migration, configuration)
    os.chmod(filepath, 0o777)
    with open(filepath, "a") as file:
        file.write("# abc")

    file_state = service.get_migration(migration.name, migration.version)
    assert file_state.checksum != db_state.checksum
    recalculate_migrations_checksum(domain_event.ApplicationEvent(application=application))

    db_state = application.session.get_migration_model_by_version(migration.version)
    file_state = service.get_migration(migration.name, migration.version)
    assert file_state.checksum == db_state.checksum


def test_raise_if_migrations_checksum_mismatch(
    migration: domain_migration.Migration,
    configuration: config.Config,
    application: applications.MigrationApp,
) -> None:
    service = migration_service.MigrationService(application.session)
    service.create_migration_file_template(migration.name, migration.version)
    migration = service.get_migration(migration.name, migration.version)

    application.session.append_migration(migration)

    file_state = service.get_migration(migration.name, migration.version)
    db_state = application.session.get_migration_model_by_version(migration.version)

    assert file_state.checksum == db_state.checksum

    filepath = tools.get_migration_file_path(migration, configuration)
    os.chmod(filepath, 0o777)
    with open(filepath, "a") as file:
        file.write("# abc")

    with pytest.raises(domain_exception.MigrationFileChangedError):
        raise_if_migrations_checksum_mismatch(
            domain_event.ApplicationEvent(application=application)
        )
