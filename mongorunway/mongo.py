from __future__ import annotations

__all__: typing.Sequence[str] = (
    "DocumentType",
    "Client",
    "Database",
    "Collection",
    "ClientSession",
)

import typing

import pymongo
from pymongo import client_session
from pymongo import database

DocumentType: typing.TypeAlias = typing.Dict[str, typing.Any]

Client = pymongo.MongoClient[DocumentType]

Database = database.Database[DocumentType]

Collection = pymongo.collection.Collection[DocumentType]

ClientSession = client_session.ClientSession
