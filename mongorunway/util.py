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
r"""Utilities.

The module contains utilities that can be used in a project.

Notes
-----
This module is independent of all other modules and can only use
built-in or third-party libraries.
"""

from __future__ import annotations

__all__: typing.Sequence[str] = (
    "get_module",
    "as_snake_case",
    "import_obj",
    "convert_string",
    "build_mapping_values",
    "build_optional_kwargs",
    "is_valid_filename",
    "hexlify",
)

import binascii
import copy
import distutils.util
import importlib
import importlib.util
import os
import re
import time
import types
import typing

import bson

_P = typing.ParamSpec("_P")
_T = typing.TypeVar("_T")

string_case_pattern: typing.Final[typing.Pattern[str]] = re.compile(
    r"""
    (?<=_)     # Positive lookbehind assertion for an underscore character
    (\w+)      # Match and capture one or more word characters (alphanumeric or underscore)
    |          # Or
    ([A-Z][a-z]+)   # Match and capture an uppercase letter followed by one or more lowercase letters
    |          # Or
    ([a-z]+)   # Match and capture one or more lowercase letters
    (?=[A-Z])  # Positive lookahead assertion for an uppercase letter
    """,
    flags=re.VERBOSE,
)
r"""Regular expression for string cases.

The `string_case_pattern` constant is a regular expression pattern 
used for matching different cases in strings.
"""

number_pattern: typing.Final[typing.Pattern[str]] = re.compile(
    r"""
    [-+]?                    # Matches an optional sign character (- or +)
    (?:                       # Non-capturing group:
       \d{1,3}                # Matches 1 to 3 digits
       (?:_\d{3})*            # Matches an underscore (_) followed by exactly 3 digits, 
                              #                             repeated zero or more times.
       |                      # Alternation operator, allows matching either the previous pattern 
                              #                                         or the following pattern.
       [\d_]+                 # Matches one or more digits or underscores
       (?:\.\d+)?             # Matches an optional decimal part, where \.\d+ matches a dot 
                              #                                 followed by one or more digits.
    )
    """,
    flags=re.VERBOSE,
)
r"""Regular expression for numeric values.

The number_pattern constant is a regular expression pattern used for 
matching numeric values.
"""


@typing.overload
def convert_string(val: typing.Literal["true", "yes", "ok"], /) -> typing.Literal[True]:
    ...


@typing.overload
def convert_string(val: typing.Literal["false", "no"], /) -> typing.Literal[False]:
    ...


@typing.overload
def convert_string(val: typing.Literal["none", "nothing", "undefined"], /) -> typing.Literal[None]:
    ...


def convert_string(value: str, /) -> typing.Union[int, float, bool, str, None]:
    r"""Converts a string.

    Converts a string depending on the received value. Case-insensitive
    string conversion. If the string fails all the checks, the passed
    value will be returned.

    Parameters
    ----------
    value : str
        The value that needs to be converted.

    Returns
    -------
    typing.Union[int, float, bool, str, None]
        None, if the value is one of {"none", "nothing", "undefined"}.

    See Also
    --------
    number_pattern : Relationship.
    distutils.util.strtobool : Relationship.
    """
    if not isinstance(value, str):
        return value

    value_lower = value.lower().strip()
    if value_lower in {"none", "nothing", "undefined"}:
        return None

    if digit_matches := re.findall(number_pattern, value_lower):
        # For floating point numbers.
        if len(digit_matches) > 1:
            # Floating-point numbers should not have more than one decimal point.
            digit_matches = digit_matches[:2]

            # To handle numbers that use an underscore.
            if any(m.count("_") for m in digit_matches):
                return int("".join(digit_matches))

            return float(".".join(digit_matches))

        (digit_string,) = digit_matches
        return int(digit_string)

    try:
        integer = distutils.util.strtobool(value_lower)
    except ValueError:
        return value

    return bool(integer)


def hexlify(binary: bson.binary.Binary) -> str:
    r"""Converts a binary object to hexadecimal.

    Converts a binary object to a more user-friendly hexadecimal string.
    This method can be useful for converting session IDs in both pymongo
    and mongorunway, as these tools use the same format for identifiers.

    Parameters
    ----------
    binary : bson.binary.Binary
        Binary representation of the object to be converted to a hexadecimal
        string.

    Returns
    -------
    str
        The converted binary object as a hexadecimal string.
    """
    hex_id = binascii.hexlify(binary).decode()
    return hex_id


def build_mapping_values(
    mapping: typing.MutableMapping[_T, typing.Any], /
) -> typing.MutableMapping[_T, typing.Any]:
    r"""Converts string values in a mutable mapping.

    Converts string values in a mutable mapping to corresponding named
    objects. If a string fails validation, the original value is retained.

    Parameters
    ----------
    mapping : typing.MutableMapping[_T, typing.Any]
        Mutable mapping whose values need to be converted.

    Returns
    -------
    typing.MutableMapping[_T, typing.Any]
        Mutable mapping with converted values.

    Example
    -------
    >>> build_mapping_values({1: "undefined", 2: "ok", 3: "no"})
    {1: None, 2: True, 3: False}

    See Also
    --------
    convert_string
    """
    for key, value in copy.copy(mapping).items():
        mapping[key] = convert_string(value)

    return mapping


def build_optional_kwargs(
    keys: typing.Iterable[_T],
    mapping: typing.MutableMapping[typing.Hashable, typing.Any],
) -> typing.MutableMapping[_T, typing.Any]:
    r"""Converts string values in a mutable mapping.

    Converts string values in a mutable mapping to corresponding named
    objects. If the value of a dictionary is None, the loop will move
    to the next iteration. Returns a mutable mapping with the keys passed
    to this function.

    Parameters
    ----------
    keys : typing.Iterable[_T]
        Keys of optional values to be converted if their value is not None.
    mapping : typing.MutableMapping[typing.Hashable, typing.Any]
        Mutable mapping whose values need to be converted.

    Returns
    -------
    typing.MutableMapping[_T, typing.Any]
        Mutable mapping with all non-None values converted.

    Example
    -------
    >>> build_optional_kwargs([1, 2], {1: None, 2: "ok", 3: "no"})
    {2: True}

    See Also
    --------
    convert_string
    """
    kwargs = {}

    for key in keys:
        value = mapping.get(key)
        if value is not None:
            kwargs[key] = convert_string(value)

    return kwargs


def get_module(directory: str, filename: str) -> types.ModuleType:
    r"""Loads a module from given directory.

    Load and return a module based on the given directory and filename.
    Also supports the format without a file extension e.g. '.py' .

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
        If the file specified by `directory` and `filename` parameters
        cannot be found.

    Example
    -------
    >>> from types import ModuleType
    ... # Obtains the current file util.py when running doctest
    ... # in the current directory.
    >>> assert isinstance(get_module("", "util.py"), ModuleType)
    ...
    >>> from types import ModuleType
    ... # Also supports the format without a file extension.
    >>> assert isinstance(get_module("", "util"), ModuleType)

    See Also
    --------
    importlib.spec_from_file_location
    """
    if not filename.endswith(".py"):
        filename += ".py"

    spec = importlib.util.spec_from_file_location(
        filename.rstrip(".py"), (path := os.path.join(directory, filename))
    )
    if spec is None:
        raise ModuleNotFoundError(f"Module {path!r} is not found.")

    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None  # For type checkers only
    spec.loader.exec_module(module)
    return module


def import_obj(obj_path: str, /, cast: _T) -> _T:
    r"""Imports a class from the specified module.

    Imports a class from the specified module. The module path should
    be specified using dot notation, with the class itself at the end.

    Parameters
    ----------
    obj_path : str
        The path to the obj to be imported.
    cast : _T
        The type to which the value should be cast. This is used to
        provide more clarity in the code. This parameter is also useful
        for compatibility with type checkers.

    Returns
    -------
    _T
        The type to which we cast the imported obj.

    See Also
    --------
    importlib.import_module
    """
    module_name, obj_name = obj_path.rsplit(".", maxsplit=1)
    module = importlib.import_module(module_name)
    return typing.cast(cast, getattr(module, obj_name))


def is_valid_filename(directory: str, filename: str) -> bool:
    r"""Validates the file in the given directory.

    Check whether a given filename is a valid migration file in the
    given directory.

    Parameters
    ----------
    directory : str
        The path of the directory where the file is located.
    filename : str
        The name of the file to be checked.

    Returns
    -------
    bool
        True if the filename is a valid migration file, False otherwise.

    Raises
    ------
    ValueError
        If the value passed to the directory parameter is not a directory.

    Notes
    -----
    The function checks if a file exists in the specified directory.
    Additionally, the file must have the extension '.py' and should not
    start with a dunder [1].

    References
    ----------
    .. [1] Dunder: The term "dunder" is a short form of "double underscore"
       and is commonly used to refer to special methods or attributes in
       Python that are surrounded by double underscores on both sides, such
       as __init__ or __name__.
    """
    if not os.path.isdir(directory):
        raise ValueError(f"The specified path {directory!r} is not a directory.")

    return (
        os.path.isfile(os.path.join(directory, filename))
        and filename.endswith(".py")
        and not filename.startswith("__")
    )


def as_snake_case(obj: typing.Any) -> str:
    r"""Converts an object to snake case format.

    Converts an object to snake case format regardless of the type of the
    object passed. If the object is an instance of the `str` class, the object
    itself will be converted. Otherwise, the `obj.__name__` will be taken,
    and if it is not available, the attribute will be taken from the type of
    the object passed.

    Parameters
    ----------
    obj : typing.Any
        The object, name, or value to be converted to snake case.

    Returns
    -------
    str
        The converted name of the object or its value in snake case. It may
        return the original object if the object does not match the regular
        expression.

    Example
    -------
    >>> class DummyClass: pass
    >>> dummy_obj = DummyClass()
    >>> as_snake_case(DummyClass)
    'dummy_class'
    >>> as_snake_case(dummy_obj)  # Takes `type(dummy_obj).__name__` .
    'dummy_class'
    >>> as_snake_case("snake_case_str")
    'snake_case_str'
    >>> as_snake_case("camelCase")
    'camel_case'
    """
    if not isinstance(obj, str):
        obj_name = getattr(obj, "__name__", None)
        obj = type(obj).__name__ if obj_name is None else obj_name

    if obj.count("_"):
        # Does not support mix of string cases and skips snake case.
        return obj

    obj_match = re.findall(string_case_pattern, obj)
    obj_name = "_".join(("".join(i.lower() for i in g) for g in obj_match))

    return obj_name


def timeit_func(
    func: typing.Callable[_P, _T],
    *args: _P.args,
    **kwargs: _P.kwargs,
) -> typing.Tuple[_T, float]:
    r"""Benchmarks the execution time of a function.

    Returns the execution time of a function and the resulting output of
    calling the function with given parameters.

    Parameters
    ----------
    func : Callable[_P, _T]
        The function whose execution time needs to be benched.
    args : _P.args
        Positional arguments of a function.
    kwargs : _P.kwargs
        Keyword arguments of a function

    Returns
    -------
    Tuple[_T, float]
        A tuple where the first element is the type of the returned result
        of the function, and the second element is the time taken to execute
        the function.

    See Also
    --------
    SystemTimer
    """
    with SystemTimer() as timer:
        result = func(*args, **kwargs)

    return result, timer.executed_in


class SystemTimer:
    """Implementation of a system timer for code benchmarks.

    This class represents an implementation of a system timer for measuring
    the execution time of a specific code block. It is a context manager and
    can be conveniently used with the `with` statement.
    """

    __slots__: typing.Sequence[str] = (
        "_start",
        "_executed_in",
    )

    def __init__(self) -> None:
        self._start = 0.0
        self._executed_in = 0.0

    @property
    def start(self) -> float:
        """Returns the start time of the benchmark.

        Returns the system time that was set in the `__enter__` method of
        this class.

        Returns
        -------
        float
            The system time when the code block started execution.
        """
        return self._start

    @property
    def executed_in(self) -> float:
        """Returns the execution time of a code block.

        Returns the time it took for the code block to execute. The
        calculation is done using the system time from the `time` module.

        Returns
        -------
        float
            The execution time of the code block.
        """
        return self._executed_in

    def __enter__(self) -> SystemTimer:
        self._start = time.time()
        return self

    @typing.overload
    def __exit__(self, exc_type: None, exc_val: None, exc_tb: None) -> None:
        ...

    @typing.overload
    def __exit__(
        self,
        exc_type: typing.Type[BaseException],
        exc_val: BaseException,
        exc_tb: types.TracebackType,
    ) -> None:
        ...

    def __exit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_val: typing.Optional[BaseException],
        exc_tb: typing.Optional[types.TracebackType],
    ) -> None:
        end = time.time()
        self._executed_in = end - self.start
