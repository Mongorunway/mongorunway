from __future__ import annotations

import typing

import pymongo.database

from mongorunway.kernel.infrastructure.commands import (
    CreateDatabaseCommand,
    CreateCollectionCommand,
    DropDatabaseCommand,
    DropCollectionCommand,
)


def test_create_database_command(mongodb: pymongo.database.Database[typing.Dict[str, typing.Any]]) -> None:
    client = mongodb.client
    command = CreateDatabaseCommand(collection="skip", database="abc")

    assert command.database not in client.list_database_names()

    command.execute(client)
    assert command.database in client.list_database_names()

    client.drop_database(command.database)


def test_drop_database_command(mongodb: pymongo.database.Database[typing.Dict[str, typing.Any]]) -> None:
    client = mongodb.client
    client.abc.create_collection("skip")
    assert "abc" in client.list_database_names()

    command = DropDatabaseCommand(database="abc")
    command.execute(client)

    assert "abc" not in client.list_database_names()


def test_create_collection_command(mongodb: pymongo.database.Database[typing.Dict[str, typing.Any]]) -> None:
    command = CreateCollectionCommand("abc", mongodb.name)

    assert command.collection not in mongodb.list_collection_names()

    command.execute(mongodb.client)
    assert command.collection in mongodb.list_collection_names()


def test_drop_collection_command(mongodb: pymongo.database.Database[typing.Dict[str, typing.Any]]) -> None:
    mongodb.create_collection("abc")
    command = DropCollectionCommand("abc", mongodb.name)

    assert command.collection in mongodb.list_collection_names()

    command.execute(mongodb.client)
    assert command.collection not in mongodb.list_collection_names()
