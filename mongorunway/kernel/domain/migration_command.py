from __future__ import annotations

__all__: typing.Sequence[str] = ("MigrationCommand",)

import abc
import typing

import pymongo


class MigrationCommand(abc.ABC):
    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def execute(self, conn: pymongo.MongoClient[typing.Dict[str, typing.Any]], **kwargs: typing.Any) -> None:
        ...
