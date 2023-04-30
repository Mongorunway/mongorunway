from __future__ import annotations

__all__: typing.Sequence[str] = ("MigrationModule",)

import collections.abc
import types
import typing

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration_command import MigrationCommand


class MigrationModule:
    __slots__: typing.Sequence[str] = ("_module",)

    def __init__(self, module: types.ModuleType, /) -> None:
        self._module = module
        self._validate_business_module()

    @property
    def location(self) -> str:
        return self._module.__file__

    @property
    def description(self) -> str:
        return self._module.__doc__

    @property
    def version(self) -> int:
        return self._module.version

    def get_upgrade_commands(self) -> typing.Sequence[MigrationCommand]:
        return self._get_business_commands("upgrade")

    def get_downgrade_commands(self) -> typing.Sequence[MigrationCommand]:
        return self._get_business_commands("downgrade")

    def get_name(self) -> str:
        *_, migration_name = self._module.__name__.split(".")
        return migration_name.strip()

    def _get_business_commands(self, func_name: str, /) -> typing.Sequence[MigrationCommand]:
        func = getattr(self._module, func_name)

        if not isinstance(commands := func(), collections.abc.Sequence):
            raise ValueError(f"'{func_name}' function must return sequence of commands.")

        return commands

    def _validate_business_module(self) -> None:
        def _check_for_callable(func: types.FunctionType, /) -> None:
            if not callable(func):
                raise ValueError(f"Function '{func.__name__}' is not callable.")

        module_requirement_funcs = ("upgrade", "downgrade")
        for func_name in module_requirement_funcs:
            func = getattr(self._module, func_name, None)

            if func is None:
                raise ValueError(
                    f"Migration '{self.get_name()}' missing requirement function: '{func_name}'."
                )

            _check_for_callable(func)
