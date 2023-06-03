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

import collections.abc
import typing

import pymongo
import pytest

from mongorunway.domain import migration_context as domain_context
from mongorunway.infrastructure.commands import BulkWrite
from mongorunway.infrastructure.commands import CreateCollection
from mongorunway.infrastructure.commands import CreateDatabase
from mongorunway.infrastructure.commands import CreateIndex
from mongorunway.infrastructure.commands import CreateIndexes
from mongorunway.infrastructure.commands import DeleteMany
from mongorunway.infrastructure.commands import DeleteOne
from mongorunway.infrastructure.commands import DropCollection
from mongorunway.infrastructure.commands import DropDatabase
from mongorunway.infrastructure.commands import InsertMany
from mongorunway.infrastructure.commands import InsertOne
from mongorunway.infrastructure.commands import make_snake_case_global_alias
from mongorunway.infrastructure.commands import RenameCollection
from mongorunway.infrastructure.commands import ReplaceOne
from mongorunway.infrastructure.commands import SendCommand
from mongorunway.infrastructure.commands import UpdateMany
from mongorunway.infrastructure.commands import UpdateOne

if typing.TYPE_CHECKING:
    from mongorunway import mongo


@pytest.fixture(scope="function")
def ctx(mongodb: mongo.Database) -> domain_context.MigrationContext:
    context = domain_context.MigrationContext(
        client=mongodb.client,
        database=mongodb,
        mongodb_session_id="abc",
        mongorunway_session_id="abc",
    )
    return context


def test_make_snake_case_global_alias() -> None:
    env = {}
    assert not env

    make_snake_case_global_alias(obj=env)(CreateDatabase)
    assert "create_database" in env


def test_create_database(ctx: domain_context.MigrationContext) -> None:
    assert "abc" not in ctx.client.list_database_names()

    cmd = CreateDatabase("abc_col", "abc")
    assert cmd.database == "abc"
    assert cmd.collection == "abc_col"
    assert cmd.args == ()
    assert cmd.kwargs == {}

    cmd.execute(ctx)
    assert "abc" in ctx.client.list_database_names()

    ctx.client.drop_database("abc")


def test_drop_database(ctx: domain_context.MigrationContext) -> None:
    ctx.client["abc"].create_collection("abc")
    assert "abc" in ctx.client.list_database_names()

    cmd = DropDatabase("abc")
    assert cmd.database == "abc"
    assert cmd.args == ()
    assert cmd.kwargs == {}

    cmd.execute(ctx)
    assert "abc" not in ctx.client.list_database_names()


def test_create_collection(ctx: domain_context.MigrationContext) -> None:
    assert "abc" not in ctx.database.list_collection_names()

    cmd = CreateCollection("abc")
    assert cmd.collection == "abc"
    assert cmd.args == ()
    assert cmd.kwargs == {}

    cmd.execute(ctx)
    assert "abc" in ctx.database.list_collection_names()


def test_drop_collection(ctx: domain_context.MigrationContext) -> None:
    ctx.database.create_collection("abc")
    assert "abc" in ctx.database.list_collection_names()

    cmd = DropCollection("abc")
    assert cmd.collection == "abc"
    assert cmd.args == ()
    assert cmd.kwargs == {}

    cmd.execute(ctx)
    assert "abc" not in ctx.database.list_collection_names()


def test_insert_many(ctx: domain_context.MigrationContext) -> None:
    collection = ctx.database.get_collection("abc")
    assert collection.count_documents({}) == 0

    cmd = InsertMany("abc", [{}, {}])
    assert cmd.collection == "abc"
    assert cmd.documents == [{}, {}]
    assert cmd.args == ()
    assert cmd.kwargs == {}

    cmd.execute(ctx)
    assert collection.count_documents({}) == 2


def test_insert_one(ctx: domain_context.MigrationContext) -> None:
    collection = ctx.database.get_collection("abc")
    assert collection.count_documents({}) == 0

    cmd = InsertOne("abc", {})
    assert cmd.collection == "abc"
    assert cmd.document == {}
    assert cmd.args == ()
    assert cmd.kwargs == {}

    cmd.execute(ctx)
    assert collection.count_documents({}) == 1


def test_delete_one(ctx: domain_context.MigrationContext) -> None:
    collection = ctx.database.get_collection("abc")
    collection.insert_one({})
    assert collection.count_documents({}) == 1

    cmd = DeleteOne("abc", {})
    assert cmd.collection == "abc"
    assert cmd.filter == {}
    assert cmd.args == ()
    assert cmd.kwargs == {}

    cmd.execute(ctx)
    assert collection.count_documents({}) == 0


def test_delete_many(ctx: domain_context.MigrationContext) -> None:
    collection = ctx.database.get_collection("abc")
    collection.insert_many([{}, {}])
    assert collection.count_documents({}) == 2

    cmd = DeleteMany("abc", {})
    assert cmd.collection == "abc"
    assert cmd.filter == {}
    assert cmd.args == ()
    assert cmd.kwargs == {}

    cmd.execute(ctx)
    assert collection.count_documents({}) == 0


def test_update_one(ctx: domain_context.MigrationContext) -> None:
    collection = ctx.database.get_collection("abc")
    collection.insert_one({"_id": 1})

    cmd = UpdateOne("abc", {"_id": 1}, {"$set": {"a": 1}}, upsert=True)
    assert cmd.collection == "abc"
    assert cmd.filter == {"_id": 1}
    assert cmd.update == {"$set": {"a": 1}}
    assert cmd.args == ()
    assert cmd.kwargs == {"upsert": True}

    cmd.execute(ctx)
    assert collection.find_one({"_id": 1})["a"] == 1


def test_update_many(ctx: domain_context.MigrationContext) -> None:
    collection = ctx.database.get_collection("abc")
    collection.insert_many([{"_id": 1}, {"_id": 2}])

    cmd = UpdateMany("abc", {}, {"$set": {"a": 1}}, upsert=True)
    assert cmd.collection == "abc"
    assert cmd.filter == {}
    assert cmd.update == {"$set": {"a": 1}}
    assert cmd.args == ()
    assert cmd.kwargs == {"upsert": True}

    cmd.execute(ctx)
    assert collection.find_one({"_id": 1})["a"] == 1
    assert collection.find_one({"_id": 2})["a"] == 1


def test_replace_one(ctx: domain_context.MigrationContext) -> None:
    collection = ctx.database.get_collection("abc")
    collection.insert_many([{"_id": 1, "a": 1}])

    cmd = ReplaceOne("abc", {"a": 1}, {"b": 1})
    assert cmd.collection == "abc"
    assert cmd.filter == {"a": 1}
    assert cmd.replacement == {"b": 1}
    assert cmd.args == ()
    assert cmd.kwargs == {}

    cmd.execute(ctx)
    assert collection.find_one({"_id": 1})["b"] == 1


def test_create_index(ctx: domain_context.MigrationContext) -> None:
    collection = ctx.database.get_collection("abc")
    assert "abc_idx_1" not in collection.index_information()

    cmd = CreateIndex("abc", "abc_idx")
    assert cmd.collection == "abc"
    assert cmd.keys == "abc_idx"
    assert cmd.args == ()
    assert cmd.kwargs == {}

    cmd.execute(ctx)
    assert "abc_idx_1" in collection.index_information()


def test_create_indexes(ctx: domain_context.MigrationContext) -> None:
    collection = ctx.database.get_collection("abc")
    assert "abc_idx_1" not in collection.index_information()
    assert "cbd_idx_-1" not in collection.index_information()

    cmd = CreateIndexes(
        "abc",
        [
            pymongo.IndexModel([("abc_idx", pymongo.ASCENDING)]),
            pymongo.IndexModel([("cbd_idx", pymongo.DESCENDING)]),
        ],
    )
    assert cmd.collection == "abc"
    assert isinstance(cmd.keys, collections.abc.Sequence)
    assert cmd.args == ()
    assert cmd.kwargs == {}

    cmd.execute(ctx)
    assert "abc_idx_1" in collection.index_information()
    assert "cbd_idx_-1" in collection.index_information()


def test_rename_collection(ctx: domain_context.MigrationContext) -> None:
    ctx.database.create_collection("abc")
    assert "abc" in ctx.database.list_collection_names()

    cmd = RenameCollection("abc", "cbd")
    assert cmd.collection == "abc"
    assert cmd.new_name == "cbd"
    assert cmd.args == ()
    assert cmd.kwargs == {}

    cmd.execute(ctx)
    assert "abc" not in ctx.database.list_collection_names()
    assert "cbd" in ctx.database.list_collection_names()


def test_send_command(ctx: domain_context.MigrationContext) -> None:
    cmd = SendCommand("ping")
    assert cmd.args == ("ping",)
    assert cmd.kwargs == {}

    assert cmd.execute(ctx) == {"ok": 1.0}


def test_bulk_write(ctx: domain_context.MigrationContext) -> None:
    collection = ctx.database.get_collection("abc")
    assert collection.count_documents({}) == 0

    cmd = BulkWrite(
        "abc",
        bulk_operations=[
            pymongo.InsertOne({}),
            pymongo.InsertOne({"_id": 1, "field": 2}),
            pymongo.UpdateOne({"_id": 1}, {"$inc": {"field": 1}}),
        ],
    )
    cmd.execute(ctx)

    assert collection.count_documents({}) == 2
    assert collection.find_one({"_id": 1})["field"] == 3
