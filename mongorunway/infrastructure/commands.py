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

__all__: typing.Sequence[str] = (
    "make_snake_case_global_alias",
    "CreateDatabase",
    "DropDatabase",
    "CreateCollection",
    "DropCollection",
    "InsertMany",
    "InsertOne",
    "DeleteOne",
    "DeleteMany",
    "UpdateOne",
    "UpdateMany",
    "ReplaceOne",
    "CreateIndex",
    "CreateIndexes",
    "DropIndex",
    "DropIndexes",
    "RenameCollection",
    "SendCommand",
)

import functools
import inspect
import typing

import pymongo
from pymongo import results

from mongorunway import mongo
from mongorunway import util
from mongorunway.domain import migration_command as domain_command

if typing.TYPE_CHECKING:
    from mongorunway.domain import migration_context as domain_context

_T = typing.TypeVar("_T")
_CommandTT = typing.TypeVar("_CommandTT", bound=typing.Type[domain_command.MigrationCommand])


@typing.overload
def make_snake_case_global_alias(obj: _CommandTT) -> _CommandTT:
    ...


@typing.overload
def make_snake_case_global_alias(
    obj: typing.MutableMapping[str, typing.Any],
) -> typing.Callable[[_CommandTT], _CommandTT]:
    ...


def make_snake_case_global_alias(
    obj: typing.Union[_CommandTT, typing.MutableMapping[str, typing.Any]],
) -> typing.Union[_CommandTT, typing.Callable[[_CommandTT], _CommandTT]]:
    def decorator(
        cls: _CommandTT,
        called_without_args: bool,
    ) -> _CommandTT:
        def func(
            ctx: domain_context.MigrationContext,
            *args: typing.Any,
            **kwargs: typing.Any,
        ) -> typing.Any:
            cls_instance = cls(*args, **kwargs)
            return cls_instance.execute(ctx)

        func.__name__ = util.as_snake_case(cls)
        func.__doc__ = cls.__doc__
        func.__module__ = cls.__module__

        if called_without_args:
            globals().update({func.__name__: func})
        else:
            obj.update({func.__name__: func})

        return cls

    if inspect.isclass(obj):
        return typing.cast(
            _CommandTT,
            decorator(obj, called_without_args=True),
        )

    return typing.cast(
        typing.Callable[[_CommandTT], _CommandTT],
        functools.partial(decorator, called_without_args=False),
    )


#################################
# ~~~ CLIENT-LEVEL COMMANDS ~~~ #
#################################


@make_snake_case_global_alias
class CreateDatabase(domain_command.MigrationCommand[mongo.Database]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "collection",
        "database",
    )

    def __init__(
        self,
        collection: str,
        database: str,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs
        self.collection = collection
        self.database = database

    def execute(self, ctx: domain_context.MigrationContext) -> mongo.Database:
        database = ctx.client.get_database(self.database)
        database.create_collection(self.collection, *self.args, **self.kwargs)
        return database


@make_snake_case_global_alias
class DropDatabase(domain_command.MigrationCommand[None]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "database",
    )

    def __init__(self, database: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        self.database = database
        self.args = args
        self.kwargs = kwargs

    def execute(self, ctx: domain_context.MigrationContext) -> None:
        ctx.client.drop_database(self.database, *self.args, **self.kwargs)
        return None


###################################
# ~~~ DATABASE-LEVEL COMMANDS ~~~ #
###################################


@make_snake_case_global_alias
class CreateCollection(domain_command.MigrationCommand[mongo.Collection]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "collection",
    )

    def __init__(self, collection: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        self.collection = collection
        self.args = args
        self.kwargs = kwargs

    def execute(self, ctx: domain_context.MigrationContext) -> mongo.Collection:
        collection = ctx.database.create_collection(self.collection, *self.args, **self.kwargs)
        return collection


@make_snake_case_global_alias
class DropCollection(domain_command.MigrationCommand[None]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "collection",
    )

    def __init__(self, collection: str, *args: typing.Any, **kwargs: typing.Any) -> None:
        self.collection = collection
        self.args = args
        self.kwargs = kwargs

    def execute(self, ctx: domain_context.MigrationContext) -> None:
        ctx.database.drop_collection(self.collection, *self.args, **self.kwargs)
        return None


@make_snake_case_global_alias
class SendCommand(domain_command.MigrationCommand[typing.Any]):
    __slots__: typing.Sequence[str] = ("args", "kwargs")

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        self.args = args
        self.kwargs = kwargs

    def execute(self, ctx: domain_context.MigrationContext) -> typing.Any:
        return ctx.database.command(*self.args, **self.kwargs)


#####################################
# ~~~ COLLECTION-LEVEL COMMANDS ~~~ #
#####################################


@make_snake_case_global_alias
class BulkWrite(domain_command.MigrationCommand[results.BulkWriteResult]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "collection",
        "bulk_operations",
    )

    def __init__(
        self,
        collection: str,
        bulk_operations: typing.Sequence[
            typing.Union[
                pymongo.InsertOne,
                pymongo.UpdateOne,
                pymongo.UpdateMany,
                pymongo.DeleteOne,
                pymongo.DeleteMany,
                pymongo.ReplaceOne,
            ],
        ],
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.collection = collection
        self.bulk_operations = bulk_operations
        self.args = args
        self.kwargs = kwargs

    def execute(self, ctx: domain_context.MigrationContext) -> results.BulkWriteResult:
        collection = ctx.database.get_collection(self._collection)
        result = collection.bulk_write(self._bulk_operations, *self.args, **self.kwargs)
        return result


@make_snake_case_global_alias
class InsertOne(domain_command.MigrationCommand[results.InsertOneResult]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "document",
        "collection",
    )

    def __init__(
        self,
        collection: str,
        document: typing.Any,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs
        self.document = document
        self.collection = collection

    def execute(self, ctx: domain_context.MigrationContext) -> results.InsertOneResult:
        collection = ctx.database.get_collection(self.collection)
        result = collection.insert_one(self.document, *self.args, **self.kwargs)
        return result


@make_snake_case_global_alias
class InsertMany(domain_command.MigrationCommand[results.InsertManyResult]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "documents",
        "collection",
    )

    def __init__(
        self,
        collection: str,
        documents: typing.Iterable[typing.Any],
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs
        self.documents = documents
        self.collection = collection

    def execute(self, ctx: domain_context.MigrationContext) -> results.InsertManyResult:
        collection = ctx.database.get_collection(self.collection)
        result = collection.insert_many(self.documents, *self.args, **self.kwargs)
        return result


@make_snake_case_global_alias
class ReplaceOne(domain_command.MigrationCommand[results.UpdateResult]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "collection",
        "filter",
        "replacement",
    )

    def __init__(
        self,
        collection: str,
        filter: typing.Mapping[str, typing.Any],
        replacement: typing.Mapping[str, typing.Any],
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs
        self.filter = filter
        self.replacement = replacement
        self.collection = collection

    def execute(self, ctx: domain_context.MigrationContext) -> results.UpdateResult:
        collection = ctx.database.get_collection(self.collection)
        result = collection.replace_one(self.filter, self.replacement, *self.args, **self.kwargs)
        return result


@make_snake_case_global_alias
class UpdateOne(domain_command.MigrationCommand[results.UpdateResult]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "collection",
        "filter",
        "update",
    )

    def __init__(
        self,
        collection: str,
        filter: typing.Mapping[str, typing.Any],
        update: typing.Mapping[str, typing.Any],
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs
        self.filter = filter
        self.update = update
        self.collection = collection

    def execute(self, ctx: domain_context.MigrationContext) -> results.UpdateResult:
        collection = ctx.database.get_collection(self.collection)
        result = collection.update_one(self.filter, self.update, *self.args, **self.kwargs)
        return result


@make_snake_case_global_alias
class UpdateMany(domain_command.MigrationCommand[results.UpdateResult]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "collection",
        "filter",
        "update",
    )

    def __init__(
        self,
        collection: str,
        filter: typing.Mapping[str, typing.Any],
        update: typing.Union[
            typing.Mapping[str, typing.Any], typing.Sequence[typing.Mapping[str, typing.Any]]
        ],
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs
        self.filter = filter
        self.update = update
        self.collection = collection

    def execute(self, ctx: domain_context.MigrationContext) -> results.UpdateResult:
        collection = ctx.database.get_collection(self.collection)
        result = collection.update_many(self.filter, self.update, *self.args, **self.kwargs)
        return result


@make_snake_case_global_alias
class DeleteOne(domain_command.MigrationCommand[results.DeleteResult]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "filter",
        "collection",
    )

    def __init__(
        self,
        collection: str,
        filter: typing.Mapping[str, typing.Any],
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs
        self.filter = filter
        self.collection = collection

    def execute(self, ctx: domain_context.MigrationContext) -> results.DeleteResult:
        collection = ctx.database.get_collection(self.collection)
        result = collection.delete_one(self.filter, *self.args, **self.kwargs)
        return result


@make_snake_case_global_alias
class DeleteMany(domain_command.MigrationCommand[results.DeleteResult]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "filter",
        "collection",
    )

    def __init__(
        self,
        collection: str,
        filter: typing.Mapping[str, typing.Any],
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs
        self.filter = filter
        self.collection = collection

    def execute(self, ctx: domain_context.MigrationContext) -> results.DeleteResult:
        collection = ctx.database.get_collection(self.collection)
        result = collection.delete_many(self.filter, *self.args, **self.kwargs)
        return result


@make_snake_case_global_alias
class CreateIndex(domain_command.MigrationCommand[str]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "keys",
        "collection",
    )

    def __init__(
        self,
        collection: str,
        keys: pymongo.collection._IndexKeyHint,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs
        self.keys = keys
        self.collection = collection

    def execute(self, ctx: domain_context.MigrationContext) -> str:
        collection = ctx.database.get_collection(self.collection)
        result = collection.create_index(self.keys, *self.args, **self.kwargs)
        return result


@make_snake_case_global_alias
class CreateIndexes(domain_command.MigrationCommand[typing.List[str]]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "keys",
        "collection",
    )

    def __init__(
        self,
        collection: str,
        keys: typing.Sequence[pymongo.IndexModel],
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs
        self.keys = keys
        self.collection = collection

    def execute(self, ctx: domain_context.MigrationContext) -> typing.List[str]:
        collection = ctx.database.get_collection(self.collection)
        result = collection.create_indexes(self.keys, *self.args, **self.kwargs)
        return result


@make_snake_case_global_alias
class DropIndex(domain_command.MigrationCommand[None]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "index_or_name",
        "collection",
    )

    def __init__(
        self,
        collection: str,
        index_or_name: pymongo.collection._IndexKeyHint,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs
        self.index_or_name = index_or_name
        self.collection = collection

    def execute(self, ctx: domain_context.MigrationContext) -> None:
        collection = ctx.database.get_collection(self.collection)
        collection.drop_index(self.index_or_name, *self.args, **self.kwargs)
        return None


@make_snake_case_global_alias
class DropIndexes(domain_command.MigrationCommand[None]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "collection",
    )

    def __init__(
        self,
        collection: str,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs
        self.collection = collection

    def execute(self, ctx: domain_context.MigrationContext) -> None:
        collection = ctx.database.get_collection(self.collection)
        collection.drop_indexes(*self.args, **self.kwargs)
        return None


@make_snake_case_global_alias
class RenameCollection(domain_command.MigrationCommand[typing.MutableMapping[str, typing.Any]]):
    __slots__: typing.Sequence[str] = (
        "args",
        "kwargs",
        "new_name",
        "collection",
    )

    def __init__(
        self,
        collection: str,
        new_name: str,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> None:
        self.args = args
        self.kwargs = kwargs
        self.new_name = new_name
        self.collection = collection

    def execute(
        self,
        ctx: domain_context.MigrationContext,
    ) -> typing.MutableMapping[str, typing.Any]:
        collection = ctx.database.get_collection(self.collection)
        result = collection.rename(self.new_name, *self.args, **self.kwargs)
        return result


__aliases__: typing.List[str] = []
for name in __all__:
    try:
        if issubclass(value := globals().get(name), domain_command.MigrationCommand):
            __aliases__.append(util.as_snake_case(value))
    except TypeError:
        continue

__all__ += tuple(__aliases__)
