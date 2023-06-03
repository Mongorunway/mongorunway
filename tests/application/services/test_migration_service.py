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

import pytest

from mongorunway.application import applications
from mongorunway.application.services.migration_service import MigrationService
from mongorunway.domain import migration as domain_migration


class TestMigrationService:
    def test_create_migration_file_template(
        self,
        application: applications.MigrationApp,
        migration: domain_migration.Migration,
        migration2: domain_migration.Migration,
    ) -> None:
        service = MigrationService(application.session)

        service.create_migration_file_template(migration.name, migration.version)
        migration_from_file = service.get_migration(migration.name, migration.version)
        assert isinstance(migration_from_file, domain_migration.Migration)
        assert migration_from_file.version == 1

        # Version autoinc
        service.create_migration_file_template(migration2.name)
        assert service.get_migration(migration2.name, migration.version).version == 2

        with pytest.raises(ValueError):
            service.create_migration_file_template(
                migration_filename="abc",
                migration_version=4,
            )

        application.session.append_migration(migration)
        with pytest.raises(ValueError):
            # Migration already exist
            service.create_migration_file_template(migration.name, migration.version)

    def test_get_migration_from_filename(
        self,
        application: applications.MigrationApp,
        migration: domain_migration.Migration,
    ) -> None:
        service = MigrationService(application.session)

        service.create_migration_file_template(migration.name, migration.version)
        migration_from_file = service.get_migration(migration.name, migration.version)
        assert isinstance(migration_from_file, domain_migration.Migration)

    def test_get_migrations_from_directory(
        self,
        application: applications.MigrationApp,
        migration: domain_migration.Migration,
        migration2: domain_migration.Migration,
    ) -> None:
        service = MigrationService(application.session)
        assert len(service.get_migrations()) == 0

        service.create_migration_file_template(migration.name, migration.version)
        service.create_migration_file_template(migration2.name, migration2.version)

        assert len(service.get_migrations()) == 2
