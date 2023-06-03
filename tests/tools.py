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

from mongorunway.application.services import migration_service

if typing.TYPE_CHECKING:
    from mongorunway.application import applications
    from mongorunway.application import config
    from mongorunway.domain import migration as domain_migration


def get_migration_file_path(
    migration: domain_migration.Migration,
    configuration: config.Config,
) -> str:
    filename = configuration.filesystem.filename_strategy.transform_migration_filename(
        migration.name,
        migration.version,
    )
    return configuration.filesystem.scripts_dir + "\\" + filename + ".py"


def prepare_one_migration(
    application: applications.MigrationApp,
    migration: domain_migration.Migration,
) -> None:
    service = migration_service.MigrationService(application.session)
    service.create_migration_file_template(migration.name, migration.version)
    application.session.append_migration(migration)


def prepare_two_migrations(
    application: applications.MigrationApp,
    migration: domain_migration.Migration,
    migration2: domain_migration.Migration,
) -> None:
    prepare_one_migration(application, migration)
    prepare_one_migration(application, migration2)
