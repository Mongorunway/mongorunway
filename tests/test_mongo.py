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

import typing
from unittest import mock

import pymongo
from pymongo import client_session
from pymongo import database
import pytest

from mongorunway.mongo import Client
from mongorunway.mongo import ClientSession
from mongorunway.mongo import Collection
from mongorunway.mongo import Cursor
from mongorunway.mongo import Database
from mongorunway.mongo import DocumentType
from mongorunway.mongo import hint_or_sort_cursor
from mongorunway.mongo import translate_index


def test_document_type() -> None:
    # Base document type for mongorunway
    assert typing.get_args(DocumentType) == (str, typing.Any)


def test_database() -> None:
    assert typing.get_origin(Database) is database.Database
    assert typing.get_args(Database)[0] == typing.Dict[str, typing.Any]


def test_client() -> None:
    assert typing.get_origin(Client) is pymongo.MongoClient
    assert typing.get_args(Client)[0] == typing.Dict[str, typing.Any]


def test_collection() -> None:
    assert typing.get_origin(Collection) is pymongo.collection.Collection
    assert typing.get_args(Collection)[0] == typing.Dict[str, typing.Any]


def test_client_session() -> None:
    assert ClientSession is client_session.ClientSession


def test_cursor() -> None:
    assert typing.get_origin(Cursor) is pymongo.cursor.Cursor
    assert typing.get_args(Cursor)[0] == typing.Dict[str, typing.Any]


@pytest.mark.parametrize(
    "index, expected_result",
    [
        ([("x", 1), ("y", 2), ("z", 3)], "x_1_y_2_z_3"),
        ([("a", 10), ("b", 20)], "a_10_b_20"),
        ([], ""),
        ([("abc", 123)], "abc_123"),
        ("abc", "abc"),
        (("abc", 1), "abc_1"),
    ],
)
def test_translate_index(
    index: typing.Sequence[typing.Tuple[str, int]],
    expected_result: str,
) -> None:
    assert translate_index(index) == expected_result


class TestHintOrSortCursor:
    @pytest.fixture
    def example_cursor(self) -> Cursor:
        # Create an example Cursor object for testing
        return Cursor(mock.Mock(spec=pymongo.collection.Collection))

    def test_hint_or_sort_cursor_with_existing_index(self, example_cursor: Cursor) -> None:
        # Test when the index exists in the collection
        index_name = "example_index"

        example_cursor.collection.index_information.return_value = {index_name: {}}
        example_cursor.hint = mock.Mock()
        example_cursor.sort = mock.Mock()

        hint_or_sort_cursor(example_cursor, indexes=index_name)

        example_cursor.hint.assert_called_once_with(index_name)
        example_cursor.sort.assert_not_called()

    def test_hint_or_sort_cursor_with_missing_index(self, example_cursor: Cursor) -> None:
        # Test when the index is missing in the collection
        missing_index = "missing_index"
        example_cursor.collection.index_information.return_value = {}
        example_cursor.sort = mock.Mock()
        example_cursor.hint = mock.Mock()

        hint_or_sort_cursor(example_cursor, indexes=missing_index)

        example_cursor.sort.assert_called_once_with(missing_index)
        example_cursor.hint.assert_not_called()

    def test_hint_or_sort_cursor_with_multiple_indexes(self, example_cursor: Cursor) -> None:
        # Test with multiple indexes, some existing and some missing
        existing_index = ("existing_index", 1)
        missing_index = ("missing_index", 1)

        example_cursor.collection.index_information.return_value = {existing_index: {}}
        example_cursor.sort = mock.Mock()
        example_cursor.hint = mock.Mock()

        hint_or_sort_cursor(example_cursor, indexes=[existing_index, missing_index])

        example_cursor.sort.assert_called_once_with([existing_index, missing_index])
        example_cursor.hint.assert_not_called()

    def test_hint_or_sort_cursor_with_empty_indexes(self, example_cursor: Cursor) -> None:
        # Test when no indexes are provided
        example_cursor.collection.index_information.return_value = {}
        example_cursor.hint = mock.Mock()
        example_cursor.sort = mock.Mock()

        hint_or_sort_cursor(example_cursor, indexes=[])

        example_cursor.hint.assert_called_once_with([])
        example_cursor.sort.assert_not_called()
