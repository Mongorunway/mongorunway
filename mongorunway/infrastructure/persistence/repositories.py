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

__all__: typing.Sequence[str] = ("MongoModelRepositoryImpl",)

import enum
import threading
import typing

import pymongo

from mongorunway import mongo
from mongorunway.application.ports import repository as repository_port
from mongorunway.domain import migration as domain_migration


class Index(enum.Enum):
    UNAPPLIED = [("is_applied", pymongo.ASCENDING)]
    APPLIED = [("is_applied", pymongo.ASCENDING), ("_id", pymongo.DESCENDING)]
    UNIQUE = "_id_"

    def translate(self) -> str:
        return mongo.translate_index(self.value)


class MongoModelRepositoryImpl(repository_port.MigrationModelRepository):
    __slots__: typing.Sequence[str] = (
        "_collection",
        "_lock",
    )

    def __init__(self, migrations_collection: mongo.Collection) -> None:
        self._collection = migrations_collection
        self._lock = threading.RLock()  # Use reentrant lock to allow nested acquire/release

    def __len__(self) -> int:
        with self._lock:
            return self.has_migrations()

    def __contains__(self, item: typing.Any, /) -> bool:
        with self._lock:
            return self.has_migration(item)

    def has_migration(self, item: typing.Any, /) -> bool:
        version: typing.Optional[int] = getattr(item, "version", None)
        if version is None:
            return NotImplemented

        with self._lock:
            return self.has_migration_with_version(version)

    def has_migration_with_version(self, migration_version: int, /) -> bool:
        with self._lock:
            return self._collection.count_documents(
                {"_id": migration_version}
            ) > 0

    def has_migrations(self) -> bool:
        with self._lock:
            return bool(
                self._collection.count_documents(
                    {},
                    limit=1,
                )
            )

    def acquire_migration_model_by_version(
        self,
        migration_version: int,
    ) -> typing.Optional[domain_migration.MigrationReadModel]:
        with self._lock:
            schema = self._collection.find_one({"_id": migration_version})

        if schema is not None:
            return domain_migration.MigrationReadModel.from_dict(schema)

        return None

    def acquire_migration_model_by_flag(
        self, is_applied: bool
    ) -> typing.Optional[domain_migration.MigrationReadModel]:
        with self._lock:
            if is_applied:
                # LIFO
                schema = self._collection.find({"is_applied": True}).sort("_id", -1).limit(1)
            else:
                # FIFO
                schema = self._collection.find({"is_applied": False}).sort("_id", 1).limit(1)

        try:
            model = domain_migration.MigrationReadModel.from_dict(schema.next())
        except StopIteration:
            return None

        return model

    def acquire_migration_models_by_flag(
        self, *, is_applied: bool
    ) -> typing.Iterator[domain_migration.MigrationReadModel]:
        indexes = Index.APPLIED if is_applied else Index.UNAPPLIED
        with self._lock:
            schemas = mongo.hint_or_sort_cursor(
                self._collection.find({"is_applied": is_applied}),
                indexes=indexes.value,
            )

        while True:
            try:
                schema = schemas.next()
            except StopIteration:
                break

            yield domain_migration.MigrationReadModel.from_dict(schema)

    def acquire_all_migration_models(
        self,
        *,
        ascending_id: bool = True,
    ) -> typing.Iterator[domain_migration.MigrationReadModel]:
        with self._lock:
            if ascending_id:
                # By default, the collection has already created an index for the
                # unique key `_id` which sorts them in ascending order.
                schemas = mongo.hint_or_sort_cursor(
                    self._collection.find({}),
                    indexes=Index.UNIQUE.value,
                )

            else:
                schemas = self._collection.find({}).sort([("version", pymongo.DESCENDING)])

        while True:
            try:
                schema = schemas.next()
            except StopIteration:
                break

            yield domain_migration.MigrationReadModel.from_dict(schema)

    def append_migration(self, migration: domain_migration.Migration, /) -> int:
        schema = migration.to_dict(unique=True)

        with self._lock:
            self._collection.insert_one(
                schema,
                bypass_document_validation=True,
            )

        return migration.version

    def remove_migration(self, migration_version: int, /) -> int:
        with self._lock:
            self._collection.delete_one(
                {"_id": migration_version},
                hint=Index.UNIQUE.translate(),
            )

        return migration_version

    def set_applied_flag(self, migration: domain_migration.Migration, is_applied: bool) -> int:
        with self._lock:
            self._collection.update_one(
                {"_id": migration.version},
                {"$set": {"is_applied": is_applied}},
                bypass_document_validation=True,
            )

        return migration.version
