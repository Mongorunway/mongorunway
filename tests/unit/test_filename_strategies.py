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
