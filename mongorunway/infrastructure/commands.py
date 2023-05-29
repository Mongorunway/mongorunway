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
    "CreateCollectionCommand",
    "DropCollectionCommand",
    "CreateDatabaseCommand",
    "DropDatabaseCommand",
)

import typing

from mongorunway.domain import migration_command as domain_command

if typing.TYPE_CHECKING:
    from mongorunway.domain import migration_context as domain_context

T = typing.TypeVar("T")


class CreateCollectionCommand(domain_command.MigrationCommand):
    __slots__: typing.Sequence[str] = (
        "collection",
    )

    def __init__(self, collection: str) -> None:
        self.collection = collection

    def execute(self, ctx: domain_context.MigrationContext) -> None:
        ctx.database.create_collection(self.collection)


class DropCollectionCommand(domain_command.MigrationCommand):
    __slots__: typing.Sequence[str] = (
        "collection",
    )

    def __init__(self, collection: str) -> None:
        self.collection = collection

    def execute(self, ctx: domain_context.MigrationContext) -> None:
        ctx.database.drop_collection(self.collection)


class CreateDatabaseCommand(domain_command.MigrationCommand):
    __slots__: typing.Sequence[str] = (
        "collection",
        "database",
    )

    def __init__(self, collection: str, database: str) -> None:
        self.collection = collection
        self.database = database

    def execute(self, ctx: domain_context.MigrationContext) -> None:
        ctx.client.get_database(self.database).create_collection(self.collection)


class DropDatabaseCommand(domain_command.MigrationCommand):
    __slots__: typing.Sequence[str] = ("database",)

    def __init__(self, database: str) -> None:
        self.database = database

    def execute(self, ctx: domain_context.MigrationContext) -> None:
        ctx.client.drop_database(self.database)
