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

__all__: typing.Sequence[str] = (
    "MissingFilenameStrategy",
    "NumericalFilenameStrategy",
    "UnixFilenameStrategy",
)

import re
import time
import typing

from mongorunway.application.ports import filename_strategy as filename_strategy_port


class MissingFilenameStrategy(filename_strategy_port.FilenameStrategy):
    __slots__: typing.Sequence[str] = ()

    def is_valid_filename(self, filename: str, /) -> bool:
        return True

    def transform_migration_filename(self, filename: str, position: int) -> str:
        return filename


class NumericalFilenameStrategy(filename_strategy_port.FilenameStrategy):
    __slots__: typing.Sequence[str] = ()

    def is_valid_filename(self, filename: str, /) -> bool:
        return all(char.isdigit() for char in filename[:3])

    def transform_migration_filename(self, filename: str, position: int) -> str:
        if not self.is_valid_filename(filename):
            filename_parts = [i for i in filename.split("_") if i]
            return str(position).zfill(3) + "_" + "_".join(filename_parts)

        return filename


class UnixFilenameStrategy(filename_strategy_port.FilenameStrategy):
    __slots__: typing.Sequence[str] = ()

    def is_valid_filename(self, filename: str, /) -> bool:
        return bool(re.match(r"^\d{10,}", filename))

    def transform_migration_filename(self, filename: str, position: int) -> str:
        if not self.is_valid_filename(filename):
            filename_parts = [i for i in filename.split("_") if i]
            return str(int(time.time())) + "_" + filename_parts[0]

        return filename
