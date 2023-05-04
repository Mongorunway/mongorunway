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
"""This module contains services for working with migration versions."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "get_previous_version",
)

import typing

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration import Migration


def get_previous_version(migration: Migration) -> typing.Optional[int]:
    """Returns the version number of the previous migration of a given migration object.

    Parameters
    ----------
    migration : Migration
        The migration object for which to retrieve the previous version number.

    Returns
    -------
    Optional[int]
        The version number of the previous migration, or None if the provided migration
        object has no previous version.
    """
    return (migration.version - 1) or None
