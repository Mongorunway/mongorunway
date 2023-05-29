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

import pymongo
from pymongo import database
from pymongo import client_session

from mongorunway.mongo import DocumentType
from mongorunway.mongo import Database
from mongorunway.mongo import Client
from mongorunway.mongo import Collection
from mongorunway.mongo import ClientSession


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
