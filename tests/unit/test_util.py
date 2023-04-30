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

import datetime
import types
import typing
from unittest import mock

import pytest

from mongorunway.kernel import util


class FakeClass:
    pass


@pytest.mark.parametrize(
    "module_path, py_file_to_concat, expected_output",
    [
        ("os", None, types.ModuleType),
        ("tests.unit", "test_util", types.ModuleType)
    ],
)
def test_import_module(
    module_path: str, py_file_to_concat: typing.Optional[str], expected_output: typing.Any,
) -> None:
    with mock.patch('importlib.import_module') as mock_import_module:
        mock_import_module.return_value = expected_output

        result = util.import_module(module_path, py_file_to_concat=py_file_to_concat)

        mock_import_module.assert_called_once_with(
            f"{module_path}.{py_file_to_concat}" if py_file_to_concat else module_path
        )
        assert result == expected_output


@pytest.mark.parametrize(
    "class_path, cast, expected_output",
    [
        ("datetime.datetime", datetime.datetime, datetime.datetime),
        ("tests.unit.test_util.FakeClass", FakeClass, FakeClass)
    ],
)
def test_import_class_from_module(
    class_path: str, cast: typing.Type[typing.Any], expected_output: typing.Any,
) -> None:
    with mock.patch('importlib.import_module') as mock_import_module:
        module_name, class_name = class_path.rsplit(".", maxsplit=1)
        mock_module = mock.MagicMock()
        mock_import_module.return_value = mock_module

        mock_class = mock.MagicMock(spec=cast)
        setattr(mock_module, class_name, mock_class)

        result = util.import_class_from_module(class_path, cast=cast)

        mock_import_module.assert_called_once_with(module_name)
        assert getattr(mock_module, class_name) == mock_class
        assert result == mock_class


def test_is_valid_migration_filename() -> None:
    # Test valid migration filenames
    assert util.is_valid_migration_filename("tests/unit/", "test_util.py")

    # Test invalid migration filenames
    assert not util.is_valid_migration_filename("tests/unit/", "__init__.py")
    assert not util.is_valid_migration_filename("tests/unit/migrations/", "migration_001.txt")
    assert not util.is_valid_migration_filename("tests/unit/", "test_migrations")


def test_replace_slashes_with_dot() -> None:
    assert util.replace_slashes_with_dot("path/to/file") == "path.to.file"
    assert util.replace_slashes_with_dot("path\\to\\file") == "path.to.file"
    assert util.replace_slashes_with_dot("path//to//file") == "path.to.file"
    assert util.replace_slashes_with_dot("path/to/folder/") == "path.to.folder"
    assert util.replace_slashes_with_dot("/path/to/folder") == ".path.to.folder"
    assert util.replace_slashes_with_dot("C:\\path\\to\\file") == "C:.path.to.file"
    assert util.replace_slashes_with_dot(r"C:\path\to\file") == "C:.path.to.file"
    assert util.replace_slashes_with_dot("C:/path/to/folder/") == "C:.path.to.folder"


class TestGetModule:
    @pytest.fixture
    def filename(self) -> str:
        return "test_util.py"

    @pytest.fixture
    def filepath(self, filename: str) -> str:
        return __file__.rstrip(filename)

    def test_get_module_returns_module_instance(self, filepath: str, filename: str) -> None:
        module = util.get_module(filepath, filename)

        assert isinstance(module, types.ModuleType)

    def test_get_module_loads_module_correctly(self, filepath: str, filename: str) -> None:
        module = util.get_module(filepath, filename)

        assert hasattr(module, "FakeClass")

    def test_get_module_raises_error_if_file_not_found(self, filepath: str) -> None:
        with pytest.raises(FileNotFoundError):
            util.get_module(filepath, "nonexistent_module.py")
