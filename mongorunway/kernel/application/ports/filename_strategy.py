from __future__ import annotations

__all__: typing.Sequence[str] = (
    "FilenameStrategy",
)

import abc
import typing


class FilenameStrategy(abc.ABC):
    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def is_valid_filename(self, filename: str, /) -> bool:
        ...

    @abc.abstractmethod
    def transform_migration_filename(self, filename: str, position: int) -> str:
        ...
