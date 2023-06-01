from __future__ import annotations

__all__: typing.Sequence[str] = (
    "DocumentType",
    "Client",
    "Database",
    "Collection",
    "ClientSession",
    "Cursor",
    "hint_or_sort_cursor",
    "translate_index",
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

Cursor = pymongo.cursor.Cursor[DocumentType]


def translate_index(
    indexes: typing.Union[str, typing.Sequence[typing.Tuple[str, int]], typing.Tuple[str, int]], /
) -> str:
    if isinstance(indexes, str):
        return indexes
    if isinstance(indexes, tuple) and isinstance(indexes[0], str):
        return f"{indexes[0]}_{indexes[1]}"

    translated_index = "_".join(f"{x}_{y}" for x, y in indexes)
    return translated_index


def hint_or_sort_cursor(
    cursor: Cursor,
    /,
    indexes: typing.Union[str, typing.Sequence[typing.Tuple[str, int]]],
) -> Cursor:
    index_info = cursor.collection.index_information()
    if isinstance(indexes, str):
        if indexes not in index_info:
            return cursor.sort(indexes)
    else:
        for index in indexes:
            if isinstance(index, tuple):
                index_name, _ = index
                if index_name not in index_info:
                    return cursor.sort(indexes)

            if isinstance(index, str):
                if index not in index_info:
                    return cursor.sort(indexes)

    return cursor.hint(indexes)
