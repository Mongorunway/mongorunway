from __future__ import annotations

__all__: typing.Sequence[str] = (
    "MissingFilenameStrategy",
    "NumericalFilenameStrategy",
    "UnixFilenameStrategy",
)

import re
import time
import typing

from mongorunway.kernel.application.ports.filename_strategy import (
    FilenameStrategy,
)


class MissingFilenameStrategy(FilenameStrategy):
    __slots__: typing.Sequence[str] = ()

    def is_valid_filename(self, filename: str, /) -> bool:
        return True

    def transform_migration_filename(self, filename: str, position: int) -> str:
        return filename


class NumericalFilenameStrategy(FilenameStrategy):
    __slots__: typing.Sequence[str] = ()

    def is_valid_filename(self, filename: str, /) -> bool:
        return all(char.isdigit() for char in filename[:3])

    def transform_migration_filename(self, filename: str, position: int) -> str:
        if not self.is_valid_filename(filename):
            filename_parts = [i for i in filename.split("_") if i]
            return str(position).zfill(3) + "_" + "_".join(filename_parts)

        return filename


class UnixFilenameStrategy(FilenameStrategy):
    __slots__: typing.Sequence[str] = ()

    def is_valid_filename(self, filename: str, /) -> bool:
        return bool(re.match(r"^\d{10,}", filename))

    def transform_migration_filename(self, filename: str, position: int) -> str:
        if not self.is_valid_filename(filename):
            filename_parts = [i for i in filename.split("_") if i]
            return str(int(time.time())) + "_" + filename_parts[0]

        return filename
