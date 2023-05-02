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

import time

from mongorunway.kernel.infrastructure.filename_strategies import (
    MissingFilenameStrategy, NumericalFilenameStrategy, UnixFilenameStrategy,
)


class TestMissingFilenameStrategy:
    def test_is_valid_filename(self):
        strategy = MissingFilenameStrategy()
        assert strategy.is_valid_filename("migration.py")
        assert strategy.is_valid_filename("001_migration.py")
        assert strategy.is_valid_filename("20220502_migration.py")

    def test_transform_migration_filename(self):
        strategy = MissingFilenameStrategy()
        assert strategy.transform_migration_filename("migration.py", 1) == "migration.py"
        assert strategy.transform_migration_filename("001_migration.py", 2) == "001_migration.py"
        assert strategy.transform_migration_filename("20220502_migration.py", 3) == "20220502_migration.py"


class TestNumericalFilenameStrategy:
    def test_is_valid_filename(self):
        strategy = NumericalFilenameStrategy()
        assert strategy.is_valid_filename("001_migration.py")
        assert strategy.is_valid_filename("100_migration.py")
        assert not strategy.is_valid_filename("migration.py")

    def test_transform_migration_filename(self):
        strategy = NumericalFilenameStrategy()
        assert strategy.transform_migration_filename("migration.py", 1) == "001_migration.py"
        assert strategy.transform_migration_filename("002_migration.py", 2) == "002_migration.py"
        assert strategy.transform_migration_filename("migration.py", 3) == "003_migration.py"


class TestUnixFilenameStrategy:
    def test_is_valid_filename(self):
        strategy = UnixFilenameStrategy()
        assert strategy.is_valid_filename("1620000000_migration.py")
        assert strategy.is_valid_filename("1620000000_migration")
        assert not strategy.is_valid_filename("migration.py")

    def test_transform_migration_filename(self):
        strategy = UnixFilenameStrategy()
        assert strategy.transform_migration_filename("migration.py", 1).startswith(str(int(time.time())))
        assert strategy.transform_migration_filename("1620000000_migration.py", 2) == "1620000000_migration.py"
        assert strategy.transform_migration_filename("1620000000_migration", 3) == "1620000000_migration"
