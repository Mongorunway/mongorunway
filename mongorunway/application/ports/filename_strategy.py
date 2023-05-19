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
"""This module defines the interface for migration file naming strategies."""
from __future__ import annotations

__all__: typing.Sequence[str] = ("FilenameStrategy",)

import abc
import typing


class FilenameStrategy(abc.ABC):
    """Abstract base class for filename strategies used in migration."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def is_valid_filename(self, filename: str, /) -> bool:
        """Check if the given filename is valid for this strategy.

        Parameters
        ----------
        filename : str
            The filename to check.

        Returns
        -------
        bool
            True if the filename is valid, False otherwise.
        """
        ...

    @abc.abstractmethod
    def transform_migration_filename(self, filename: str, position: int) -> str:
        """Transform a migration filename using this strategy.

        Parameters
        ----------
        filename : str
            The filename to transform.
        position : int
            The position of the migration.

        Returns
        -------
        str
            The transformed filename.
        """
        ...
