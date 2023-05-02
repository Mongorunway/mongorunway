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

from mongorunway.kernel.infrastructure.hooks import SyncScriptsWithQueues

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration import Migration
    from mongorunway.kernel.application.ui import MigrationUI


def test_sync_scripts_with_queues(
    application: MigrationUI, migration: Migration, tmp_path: pathlib.Path,
) -> None:
    # Reloading temp migrations dir
    application.config.migration_scripts_dir = str(tmp_path)

    application.create_migration_file_template(migration.name, migration.version)

    assert len(application.pending) == 0
    assert len(application.applied) == 0

    hook = SyncScriptsWithQueues()
    hook.apply(application)

    assert len(application.pending) == 1
    assert len(application.applied) == 0
