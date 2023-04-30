from __future__ import annotations

__all__: typing.Sequence[str] = (
    "import_module",
    "import_class_from_module",
    "get_module",
    "is_valid_migration_filename",
    "replace_slashes_with_dot",
)

import importlib
import importlib.util
import os
import types
import typing

ClassT = typing.TypeVar("ClassT")


def import_module(module_path: str, *, py_file_to_concat: typing.Optional[str] = None) -> types.ModuleType:
    if py_file_to_concat is not None:
        module_path = module_path + "." + py_file_to_concat.rstrip(".py")

    return importlib.import_module(module_path)


def import_class_from_module(class_path: str, /, cast: ClassT) -> ClassT:
    module_name, class_name = class_path.rsplit(".", maxsplit=1)
    module = importlib.import_module(module_name)
    return typing.cast(cast, getattr(module, class_name))


def get_module(directory: str, filename: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(filename.rstrip(".py"), os.path.join(directory, filename))

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_valid_migration_filename(directory: str, filename: str) -> bool:
    return (
        os.path.isfile(os.path.join(directory, filename))
        and filename.endswith(".py")
        and not filename.startswith("__")
    )


def replace_slashes_with_dot(string_to_replace: str, /) -> str:
    string_to_replace = (
        string_to_replace.replace(r"//", ".")
        .replace(r"/", ".")
        .replace(r"\\", ".")
        .replace(r"\ ".strip(), ".")
    )
    if string_to_replace.endswith("."):
        return string_to_replace[:-1]

    return string_to_replace
