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

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration_command import MigrationCommand


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

    __slots__: typing.Sequence[str] = ("_module",)

    def __init__(self, module: types.ModuleType, /) -> None:
        self._module = module
        self._validate_business_module()

    @property
    def location(self) -> str:
        """Return the file path of the Python module this MigrationModule instance
        represents.

        Returns
        -------
        str
            The file path of the Python module.
        """
        return self._module.__file__

    @property
    def description(self) -> str:
        """Return the description of the Python module this MigrationModule instance
        represents.

        Returns
        -------
        str
            The description of the Python module.
        """
        return self._module.__doc__

    @property
    def version(self) -> int:
        """Return the version of the migration module.

        Returns
        -------
        int
            The version of the migration module.
        """
        return self._module.version

    def get_upgrade_commands(self) -> typing.Sequence[MigrationCommand]:
        """Get the sequence of upgrade migration commands from the business module.

        Returns
        -------
        Sequence[MigrationCommand]:
            The sequence of migration commands to be executed in order to upgrade the database.
        """
        return self._get_business_commands("upgrade")

    def get_downgrade_commands(self) -> typing.Sequence[MigrationCommand]:
        """Get the sequence of downgrade migration commands from the business module.

        Returns
        -------
        Sequence[MigrationCommand]:
            The sequence of migration commands to be executed in order to downgrade the database.
        """
        return self._get_business_commands("downgrade")

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

    def _get_business_commands(self, func_name: str, /) -> typing.Sequence[MigrationCommand]:
        """Return the business commands from the specified function name.

        Parameters
        ----------
        func_name : str
            The name of the function to retrieve business commands from.

        Returns
        -------
        typing.Sequence[MigrationCommand]
            The list of business commands from the specified function name.

        Raises
        ------
        ValueError
            If the specified function does not return a sequence of commands.
        """
        func = getattr(self._module, func_name)

        if not isinstance(commands := func(), collections.abc.Sequence):
            raise ValueError(f"'{func_name}' function must return sequence of commands.")

        return commands

    def _validate_business_module(self) -> None:
        """Validate that the business module contains required functions.

        Raises
        ------
        ValueError
            If the business module does not contain a required function or if a
            required function is not callable.
        """

        def _check_for_callable(func: types.FunctionType, /) -> None:
            if not callable(func):
                raise ValueError(f"Object '{str(func)}' is not callable.")

        module_requirement_funcs = ("upgrade", "downgrade")
        for func_name in module_requirement_funcs:
            func = getattr(self._module, func_name, None)

            if func is None:
                raise ValueError(
                    f"Migration '{self.get_name()}' missing requirement function: '{func_name}'."
                )

            _check_for_callable(func)
