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

from mongorunway.kernel.util import get_module
from mongorunway.kernel.application.config import migration_file_template
from mongorunway.kernel.domain.migration_module import MigrationModule
from mongorunway.kernel.application.services.checksum_service import calculate_migration_checksum


def test_calculate_migration_checksum(tmp_path: pathlib.Path) -> None:
    with open(tmp_path / (filename := "test.py"), "w") as f:
        f.write(
            migration_file_template.safe_substitute(
                version=-1,
                upgrade_commands=[],
                downgrade_commands=[],
            )
        )

    module = MigrationModule(get_module(str(tmp_path), filename))

    assert calculate_migration_checksum(module) == "f8210f7ad9a86f6cf40fe718e72a7691"
