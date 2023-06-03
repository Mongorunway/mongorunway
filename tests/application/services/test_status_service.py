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

import pathlib

import pytest

from mongorunway.application import applications
from mongorunway.application.services import migration_service
from mongorunway.application.services.status_service import check_if_all_pushed_successfully
from mongorunway.domain import migration as domain_migration


@pytest.fixture(scope="function")
def applied_migration() -> domain_migration.Migration:
    return domain_migration.Migration(
        checksum="123",
        description="123",
        downgrade_process=domain_migration.MigrationProcess(
            commands=[],
            migration_version=1,
            name="downgrade",
        ),
        upgrade_process=domain_migration.MigrationProcess(
            commands=[],
            migration_version=1,
            name="upgrade",
        ),
        version=1,
        name="123",
        is_applied=True,
    )


def test_check_all_pushed_successfully(
    application: applications.MigrationApp,
    migration2: domain_migration.Migration,
    applied_migration: domain_migration.Migration,
    tmp_path: pathlib.Path,
) -> None:
    with pytest.raises(ValueError):
        # Migrations directory is empty
        assert not check_if_all_pushed_successfully(application)

    service = migration_service.MigrationService(application.session)
    service.create_migration_file_template(applied_migration.name, applied_migration.version)

    with pytest.raises(ValueError):
        # Applied migrations is not set
        assert not check_if_all_pushed_successfully(application)

    application.session.append_migration(applied_migration)

    assert check_if_all_pushed_successfully(application)
    assert check_if_all_pushed_successfully(application, depth=1)

    service.create_migration_file_template(migration2.name, migration2.version)

    # Pushed only one of two migrations
    assert not check_if_all_pushed_successfully(application)

    # Checking only if one migration is pushed
    assert check_if_all_pushed_successfully(application, depth=1)
