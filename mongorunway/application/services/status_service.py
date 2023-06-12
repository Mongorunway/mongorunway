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

__all__: typing.Sequence[str] = ("check_if_all_pushed_successfully",)

import typing

from mongorunway.application.services import migration_service

if typing.TYPE_CHECKING:
    from mongorunway.application import applications


def check_if_all_pushed_successfully(
    application: applications.MigrationApp,
    *,
    depth: int = -1,
) -> bool:
    service = migration_service.MigrationService(application.session)

    directory_state = service.get_migrations()
    if not directory_state:
        raise ValueError("Migration files does not exist.")

    applied_state = application.session.get_migration_models_by_flag(is_applied=True)
    if not applied_state:
        raise ValueError("There are currently no applied migrations.")

    if depth > 0:
        if depth > (dir_length := len(directory_state)):
            raise ValueError(
                f"Depth ({depth}) cannot be more than migration files count ({dir_length})."
            )

        return len(directory_state[:depth]) == len(applied_state[:depth])

    return len(directory_state) == len(applied_state)
