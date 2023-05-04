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
import typing

import pytest

from mongorunway.kernel.application.services.status_service import check_if_all_pushed_successfully

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration import Migration
    from mongorunway.kernel.application.ui import MigrationUI


def test_check_all_pushed_successfully(
    application: MigrationUI, migration: Migration, migration2: Migration, tmp_path: pathlib.Path,
) -> None:
    # Reloading temp migrations dir
    application.config.migration_scripts_dir = str(tmp_path)

    with pytest.raises(ValueError):
        # Migrations directory is empty
        assert not check_if_all_pushed_successfully(application)

    application.create_migration_file_template(migration.name, migration.version)

    with pytest.raises(ValueError):
        # Applied migrations is not set
        assert not check_if_all_pushed_successfully(application)

    application.applied.append_migration(migration)

    assert check_if_all_pushed_successfully(application)
    assert check_if_all_pushed_successfully(application, depth=1)

    application.create_migration_file_template(migration2.name, migration2.version)

    # Pushed only one of two migrations
    assert not check_if_all_pushed_successfully(application)

    # Checking only if one migration is pushed
    assert check_if_all_pushed_successfully(application, depth=1)
