from __future__ import annotations

__all__: typing.Sequence[str] = (
    "CreateCollectionCommand",
    "DropCollectionCommand",
    "CreateDatabaseCommand",
    "DropDatabaseCommand",
    "create_collection",
    "drop_collection",
    "create_database",
    "drop_database",
    "cli_aware",
)

import functools
import inspect
import typing

import pymongo

from mongorunway import CLI_EXTRA_KWARGS
from mongorunway.kernel.domain.migration_command import MigrationCommand


def intersect_with_cli_args(command: MigrationCommand, /) -> typing.Mapping[str, typing.Any]:
    resolved_kwargs = {}
    command_constructor = inspect.Signature.from_callable(command.__init__)
    for parameter in command_constructor.parameters.values():
        if (parameter_value := getattr(command, parameter.name)) is None:
            cmd_vars = CLI_EXTRA_KWARGS.get()
            if (parameter_value := cmd_vars.get(parameter.name)) is None:
                raise ValueError(f"Varname {parameter.name!r} must be specified manually or as cli argument.")

        resolved_kwargs[parameter.name] = parameter_value

    return resolved_kwargs


def cli_aware(cmd):
    @functools.wraps(cmd)
    def wrapper(self, *args):
        kwargs = intersect_with_cli_args(self)
        return cmd(self, *args, **kwargs)

    return wrapper


class CreateCollectionCommand(MigrationCommand):
    __slots__: typing.Sequence[str] = (
        "collection_name",
        "database_name",
    )

    def __init__(
        self,
        collection_name: typing.Optional[str] = None,
        database_name: typing.Optional[str] = None,
    ) -> None:
        self.collection_name = collection_name
        self.database_name = database_name

    @cli_aware
    def execute(self, conn: pymongo.MongoClient[typing.Dict[str, typing.Any]], **kwargs: typing.Any) -> None:
        db = conn.get_database(kwargs["database_name"])
        db.create_collection(kwargs["collection_name"])


class DropCollectionCommand(MigrationCommand):
    __slots__: typing.Sequence[str] = (
        "collection_name",
        "database_name",
    )

    def __init__(
        self,
        collection_name: typing.Optional[str] = None,
        database_name: typing.Optional[str] = None,
    ) -> None:
        self.collection_name = collection_name
        self.database_name = database_name

    @cli_aware
    def execute(self, conn: pymongo.MongoClient[typing.Dict[str, typing.Any]], **kwargs) -> None:
        db = conn.get_database(kwargs["database_name"])
        db.drop_collection(kwargs["collection_name"])


class CreateDatabaseCommand(MigrationCommand):
    __slots__: typing.Sequence[str] = (
        "collection_name",
        "database_name",
    )

    def __init__(
        self,
        collection_name: typing.Optional[str] = None,
        database_name: typing.Optional[str] = None,
    ) -> None:
        self.collection_name = collection_name
        self.database_name = database_name

    @cli_aware
    def execute(self, conn: pymongo.MongoClient[typing.Dict[str, typing.Any]], **kwargs: typing.Any) -> None:
        conn.get_database(kwargs["database_name"]).create_collection(kwargs["collection_name"])


class DropDatabaseCommand(MigrationCommand):
    __slots__: typing.Sequence[str] = ("database_name",)

    def __init__(self, database_name: typing.Optional[str] = None) -> None:
        self.database_name = database_name

    @cli_aware
    def execute(self, conn: pymongo.MongoClient[typing.Dict[str, typing.Any]], **kwargs: typing.Any) -> None:
        conn.drop_database(kwargs["database_name"])


create_collection = CreateCollectionCommand
drop_collection = DropCollectionCommand
create_database = CreateDatabaseCommand
drop_database = DropDatabaseCommand
