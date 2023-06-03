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
from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_exception as domain_exception
from tests import tools


class TestMigrationApp:
    def test_downgrade_once(
        self,
        application: applications.MigrationApp,
        migration: domain_migration.Migration,
    ) -> None:
        tools.prepare_one_migration(application, migration)
        with pytest.raises(domain_exception.NothingToDowngradeError):
            application.downgrade_once()

        application.upgrade_once()
        assert application.session.get_current_version() == 1

        application.downgrade_once()
        assert application.session.get_current_version() is None

    def test_upgrade_once(
        self,
        application: applications.MigrationApp,
        migration: domain_migration.Migration,
    ) -> None:
        tools.prepare_one_migration(application, migration)
        assert application.session.get_current_version() is None

        application.upgrade_once()
        assert application.session.get_current_version() == 1

        with pytest.raises(domain_exception.NothingToUpgradeError):
            application.upgrade_once()

    def test_downgrade_to(
        self,
        application: applications.MigrationApp,
        migration: domain_migration.Migration,
        migration2: domain_migration.Migration,
    ) -> None:
        tools.prepare_two_migrations(application, migration, migration2)

        with pytest.raises(ValueError):
            application.downgrade_to(1)

        with pytest.raises(ValueError):
            application.downgrade_to(4583738574)

        application.upgrade_all()
        assert application.session.get_current_version() == 2

        application.downgrade_to(1)
        assert application.session.get_current_version() == 1

    def test_upgrade_to(
        self,
        application: applications.MigrationApp,
        migration: domain_migration.Migration,
        migration2: domain_migration.Migration,
    ) -> None:
        tools.prepare_two_migrations(application, migration, migration2)

        with pytest.raises(ValueError):
            application.upgrade_to(3)

        assert application.session.get_current_version() is None
        application.upgrade_to(1)
        assert application.session.get_current_version() == 1

        application.upgrade_to(2)
        assert application.session.get_current_version() == 2

    def test_downgrade_all(
        self,
        application: applications.MigrationApp,
        migration: domain_migration.Migration,
        migration2: domain_migration.Migration,
    ) -> None:
        tools.prepare_two_migrations(application, migration, migration2)

        with pytest.raises(domain_exception.NothingToDowngradeError):
            application.downgrade_all()

        application.upgrade_all()
        assert application.session.get_current_version() == 2

        application.downgrade_all()
        assert application.session.get_current_version() is None

    def test_upgrade_all(
        self,
        application: applications.MigrationApp,
        migration: domain_migration.Migration,
        migration2: domain_migration.Migration,
    ) -> None:
        tools.prepare_two_migrations(application, migration, migration2)

        assert application.session.get_current_version() is None

        application.upgrade_all()
        assert application.session.get_current_version() == 2

    def test_downgrade_while(
        self,
        application: applications.MigrationApp,
        migration: domain_migration.Migration,
        migration2: domain_migration.Migration,
    ) -> None:
        tools.prepare_two_migrations(application, migration, migration2)

        with pytest.raises(domain_exception.NothingToDowngradeError):
            application.downgrade_while(lambda m: True)

        assert application.session.get_current_version() is None

        application.upgrade_all()
        application.downgrade_while(lambda m: m.version != 1)
        assert application.session.get_current_version() == 1

        application.downgrade_while(lambda m: m.version is not None)
        assert application.session.get_current_version() is None

    def test_upgrade_while(
        self,
        application: applications.MigrationApp,
        migration: domain_migration.Migration,
        migration2: domain_migration.Migration,
    ) -> None:
        tools.prepare_two_migrations(application, migration, migration2)
        assert application.session.get_current_version() is None

        application.upgrade_while(lambda m: m.version != 2)
        assert application.session.get_current_version() == 1

        application.upgrade_while(lambda m: m.version <= 2)
        assert application.session.get_current_version() == 2
