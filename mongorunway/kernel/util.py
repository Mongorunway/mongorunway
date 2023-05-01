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
"""This module contains a set of utilities for use in the MongoDB database migration tool."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "import_class_from_module",
    "get_module",
    "is_valid_migration_filename",
)

import importlib
import importlib.util
import os
import types
import typing

ClassT = typing.TypeVar("ClassT")


def import_class_from_module(class_path: str, /, cast: ClassT) -> ClassT:
    """Import and return the specified class from the specified module.

    Parameters
    ----------
    class_path : str
        The path to the class to import in the form "module.submodule.ClassName".
    cast : Type[ClassT]
        The type of the class to be returned.

    Returns
    -------
    ClassT
        The imported class.

    Raises
    ------
    AttributeError
        If the specified class does not exist in the module.
    ImportError
        If the specified module cannot be found or imported.
    """
    module_name, class_name = class_path.rsplit(".", maxsplit=1)
    module = importlib.import_module(module_name)
    return typing.cast(cast, getattr(module, class_name))


def get_module(directory: str, filename: str) -> types.ModuleType:
    """Load and return a module based on the given directory and filename.

    Parameters
    ----------
    directory : str
        The path to the directory where the file is located.
    filename : str
        The name of the file containing the module.

    Returns
    -------
    types.ModuleType
        The module object that is loaded from the file.

    Raises
    ------
    ModuleNotFoundError
        If the file specified by `filename` cannot be found.
    """
    if not filename.endswith(".py"):
        filename += ".py"

    spec = importlib.util.spec_from_file_location(filename.rstrip(".py"), os.path.join(directory, filename))

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_valid_migration_filename(directory: str, filename: str) -> bool:
    """Check whether a given filename is a valid migration file in the given directory.

    Parameters
    ----------
    directory : str
        The path of the directory where the file is located.
    filename : str
        The name of the file to be checked.

    Returns
    -------
    builtins.bool
        builtins.True if the filename is a valid migration file, builtins.False otherwise.
        A valid migration file  is a Python file (ends with '.py') that is not a special
        file (does not start with '__') and exists in the specified directory.
    """
    return (
        os.path.isfile(os.path.join(directory, filename))
        and filename.endswith(".py")
        and not filename.startswith("__")
    )
