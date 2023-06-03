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

from mongorunway import util
from mongorunway.application.services import migration_service
from mongorunway.application.services.checksum_service import calculate_migration_checksum
from mongorunway.domain import migration_business_module as domain_module


def test_calculate_template_migration_checksum(tmp_path: pathlib.Path) -> None:
    with open(tmp_path / (filename := "test.py"), "w") as f:
        f.write(
            migration_service.migration_file_template.safe_substitute(
                version=-1,
                upgrade_commands=[],
                downgrade_commands=[],
            )
        )

    module = domain_module.MigrationBusinessModule(util.get_module(str(tmp_path), filename))
    assert calculate_migration_checksum(module) == "26c2b7999e05d43ebd8f35f40d0f3af3"
