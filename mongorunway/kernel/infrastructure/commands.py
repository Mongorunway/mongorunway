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
"""Module for implementing database migration commands.
This module contains classes that implement database migration commands. Each command performs
a specific action, such as creating or dropping a collection.

The command classes inherit from the abstract class MigrationCommand and must implement the execute
method, which performs the corresponding action in the database.
"""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "CreateCollectionCommand",
    "DropCollectionCommand",
    "CreateDatabaseCommand",
    "DropDatabaseCommand",
)

import typing

import pymongo

from mongorunway.kernel.domain.migration_command import MigrationCommand

T = typing.TypeVar("T")


class CreateCollectionCommand(MigrationCommand):
    """A migration command that creates a collection in a MongoDB database.

    Parameters
    ----------
    collection : str
        The name of the collection to be created.
    database : str
        The name of the database where the collection will be created.
    """

    __slots__: typing.Sequence[str] = (
        "collection",
        "database",
    )

    def __init__(self, collection: str, database: str) -> None:
        self.collection = collection
        self.database = database

    def execute(self, conn: pymongo.MongoClient[typing.Dict[str, typing.Any]]) -> None:
        """Execute the command by creating a new collection in the specified database.

        Parameters
        ----------
        conn : MongoClient[typing.Dict[str, typing.Any]]
            MongoClient instance connected to the MongoDB server.
        """
        db = conn.get_database(self.database)
        db.create_collection(self.collection)


class DropCollectionCommand(MigrationCommand):
    """A class representing a migration command that drops a collection from a database.

    Parameters
    ----------
    collection : str
        The name of the collection to be dropped.
    database : str
        The name of the database containing the collection to be dropped.
    """

    __slots__: typing.Sequence[str] = (
        "collection",
        "database",
    )

    def __init__(self, collection: str, database: str) -> None:
        self.collection = collection
        self.database = database

    def execute(self, conn: pymongo.MongoClient[typing.Dict[str, typing.Any]]) -> None:
        """Drops the collection from the specified database.

        Parameters
        ----------
        conn : MongoClient[typing.Dict[str, typing.Any]]
            MongoClient instance connected to the MongoDB server.
        """
        db = conn.get_database(self.database)
        db.drop_collection(self.collection)


class CreateDatabaseCommand(MigrationCommand):
    """Command to create a database and a collection in it.

    Parameters
    ----------
    collection : str
        Name of the collection to be created in the database.
    database : str
        Name of the database where the collection will be created.
    """

    __slots__: typing.Sequence[str] = (
        "collection",
        "database",
    )

    def __init__(self, collection: str, database: str) -> None:
        self.collection = collection
        self.database = database

    def execute(self, conn: pymongo.MongoClient[typing.Dict[str, typing.Any]]) -> None:
        """Execute the command to create a database and a collection in it.

        Parameters
        ----------
        conn : MongoClient[typing.Dict[str, typing.Any]]
            MongoClient instance connected to the MongoDB server.
        """
        conn.get_database(self.database).create_collection(self.collection)


class DropDatabaseCommand(MigrationCommand):
    """A migration command that drops a MongoDB database.

    Parameters
    ----------
    database :
        The name of the database to drop.
    """

    __slots__: typing.Sequence[str] = ("database",)

    def __init__(self, database: str) -> None:
        self.database = database

    def execute(self, conn: pymongo.MongoClient[typing.Dict[str, typing.Any]]) -> None:
        """Executes the drop database command.

        Parameters
        ----------
        conn : MongoClient[typing.Dict[str, typing.Any]]
            MongoClient instance connected to the MongoDB server.
        """
        conn.drop_database(self.database)
