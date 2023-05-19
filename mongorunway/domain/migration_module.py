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
"""The MigrationModule module provides an implementation of a business module for a
migration application. This module is a wrapper around a Python module that contains
the implementation of migration commands.
"""
from __future__ import annotations

__all__: typing.Sequence[str] = ("MigrationModule",)

import collections.abc
import types
import typing

from mongorunway.domain import migration as domain_migration

if typing.TYPE_CHECKING:
    from mongorunway.domain import migration_command as domain_command


class MigrationModule:
    """Class for encapsulating a Python module that implements migration commands for
     a migration application.

    Parameters
    ----------
    module : types.ModuleType
        The Python module containing the implementation of migration commands.

    Raises
    ------
    ValueError
        If the provided `module` does not have the required 'downgrade' and 'upgrade'
        functions or if the functions are not callable.
    """

    __slots__: typing.Sequence[str] = (
        "_module",
        "_upgrade_process",
        "_downgrade_process",
    )

    def __init__(self, module: types.ModuleType, /) -> None:
        self._module = module
        self._upgrade_process = self._get_business_process("upgrade")
        self._downgrade_process = self._get_business_process("downgrade")

    @property
    def location(self) -> str:
        """Return the file path of the Python module this MigrationModule instance
        represents.

        Returns
        -------
        str
            The file path of the Python module.
        """
        return self._module.__file__ or ""

    @property
    def description(self) -> str:
        """Return the description of the Python module this MigrationModule instance
        represents.

        Returns
        -------
        str
            The description of the Python module.
        """
        return self._module.__doc__ or ""

    @property
    def version(self) -> int:
        """Return the version of the migration module.

        Returns
        -------
        int
            The version of the migration module.
        """
        return typing.cast(int, self._module.version)

    @property
    def upgrade_process(self) -> domain_migration.MigrationProcess:
        return self._upgrade_process

    @property
    def downgrade_process(self) -> domain_migration.MigrationProcess:
        return self._downgrade_process

    def get_name(self) -> str:
        """Returns the name of the migration module.

        Returns
        -------
        str
            The name of the migration module.

        Example
        -------
        # This example does not take into account the implementation of the commands necessary
        # for the functioning of the migration module, such as "upgrade" and "downgrade"
        >>> migration_module = MigrationModule(types.ModuleType("my.beautiful.ModuleName"))
        >>> migration_module.get_name()
        'ModuleName'
        """
        *_, migration_name = self._module.__name__.split(".")
        return migration_name.strip()

    def _get_business_process(self, process_name: str, /) -> domain_migration.MigrationProcess:
        process = getattr(self._module, process_name, None)
        if process is None:
            raise ValueError(
                f"Can't find {process_name!r} process in {self.get_name()!r} migration."
            )

        # if not callable(process):
        #     raise ValueError(f"Process {process_name!r} must be callable.")

        # if not isinstance(process, domain_migration.MigrationProcess):
        #     raise ValueError(
        #         f"{process!r} should return instance "
        #         f"of {domain_migration.MigrationProcess!r}."
        #     )

        return process
