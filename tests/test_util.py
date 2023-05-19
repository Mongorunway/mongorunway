from __future__ import annotations

import typing
import types

import pytest

from mongorunway.util import try_convert_string
from mongorunway.util import build_mapping_values
from mongorunway.util import build_optional_kwargs
from mongorunway.util import get_module
from mongorunway.util import is_valid_migration_filename


@pytest.mark.parametrize("value, expected", [
    ("True", True),
    ("true", True),
    ("yes", True),
    ("ok", True),
    ("False", False),
    ("false", False),
    ("no", False),
    ("None", None),
    ("none", None),
    ("nothing", None),
    ("undefined", None),
    ("42", 42),
    ("0", 0),
    ("-10", -10),
    ("hello", "hello"),
    ("   true   ", True),
    ("   FALSE   ", False),
    ("  none  ", None),
    ("  42  ", 42),
    ("  hello  ", "hello")
])
def test_try_convert_string(value: str, expected: typing.Any) -> None:
    assert try_convert_string(value) == expected


@pytest.mark.parametrize("mapping, expected", [
    (
        {
            "key1": "true",
            "key2": "42",
            "key3": "hello",
            "key4": "none"
        },
        {
            "key1": True,
            "key2": 42,
            "key3": "hello",
            "key4": None
        }
    ),
    (
        {
            "key1": "false",
            "key2": "0",
            "key3": "world",
            "key4": "undefined"
        },
        {
            "key1": False,
            "key2": 0,
            "key3": "world",
            "key4": None
        }
    ),
])
def test_build_mapping_values(
    mapping: typing.MutableMapping[str, typing.Any],
    expected: typing.MutableMapping[str, typing.Any],
) -> None:
    result = build_mapping_values(mapping)
    assert result == expected


@pytest.mark.parametrize("keys, expected", [
    (["key1"], {"key1": True}),
    (["key2"], {"key2": 42}),
    (["key3"], {"key3": "hello"}),
    (["key4"], {"key4": None}),
    (["key1", "key2"], {"key1": True, "key2": 42}),
    (["key2", "key3"], {"key2": 42, "key3": "hello"}),
    (["key1", "key3", "key4"], {"key1": True, "key3": "hello", "key4": None}),
    ([], {}),
    (["nonexistent"], {}),
])
def test_build_optional_kwargs(
    keys: typing.Iterable[str], expected: typing.MutableMapping[str, typing.Any],
) -> None:
    mapping = {
        "key1": "true",
        "key2": "42",
        "key3": "hello",
        "key4": "none"
    }
    result = build_optional_kwargs(keys, mapping)
    assert result == expected


@pytest.mark.parametrize("filename, content", [
    ("module1.py", "def add(a, b):\n    return a + b"),
    ("module2.py", "def multiply(a, b):\n    return a * b"),
])
def test_get_module(filename, content, tmp_path):
    with open(str(tmp_path / filename), "w") as f:
        f.write(content)

    module = get_module(str(tmp_path), filename)

    assert isinstance(module, types.ModuleType)
    assert hasattr(module, "add") or hasattr(module, "multiply")


@pytest.mark.parametrize("filename, expected", [
    ("migration.py", True),
    ("migration.sql", False),
    ("__init__.py", False),
])
def test_is_valid_migration_filename(filename, expected, tmp_path):
    with open(str(tmp_path / filename), "w"):
        assert is_valid_migration_filename(str(tmp_path), filename) == expected
