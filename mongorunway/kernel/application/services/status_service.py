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
"""This module contains services for monitoring migration statuses."""
from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.ui import MigrationUI


def check_if_all_pushed_successfully(application: MigrationUI, /, *, depth: int = -1) -> bool:
    """Check if all migrations have been successfully applied.

    Parameters
    ----------
    application : MigrationUI
        The MigrationUI object to check.
    depth : int, optional
        The depth to check. If set to -1 (default), all migrations will be checked.
        If set to a positive integer, only the first `depth` migrations will be checked.

    Raises
    ------
    ValueError
        If no migration files exist, no migration has been applied, or the depth is greater
        than the number of migration files.

    Returns
    -------
    bool
        True if all migrations have been successfully applied, False otherwise.

    Notes
    -----
    >>> Applied Migrations: []
    >>> Migration Files: [Migration, Migration]
    >>> check_if_all_pushed_successfully(app)
    False

    >>> Applied Migration: [Migration]
    >>> Migration Files: [Migration, Migration]
    >>> check_if_all_pushed_successfully(app)
    False  # Because Applied Migrations length != Migration Files length

    >>> Applied Migration: [Migration]
    >>> Migration Files: [Migration, Migration]
    >>> check_if_all_pushed_successfully(app, depth=1)  # Check if one migration applied successfully
    True

    This option can be useful when you are using the upgrade_once / upgrade_to / upgrade_while methods
    and need to check the status of multiple migrations. Normally this option should not be used as all
    migrations must be fully applied sequentially
    """
    directory_state = application.get_migrations_from_directory()
    if not directory_state:
        raise ValueError("Migration files does not exist.")

    applied_state = application.applied.acquire_all_migrations()
    if not applied_state:
        raise ValueError("No migration applied.")

    if depth:
        if depth > (dir_length := len(directory_state)):
            raise ValueError(
                f"Depth ({depth}) cannot be more than migration files count ({dir_length})."
            )

        return len(directory_state[:depth]) == len(applied_state[:depth])

    return len(directory_state) == len(applied_state)
