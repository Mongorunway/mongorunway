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
"""Module provides an interface to execute database migration commands."""
from __future__ import annotations

import abc
import typing

import pymongo


class MigrationCommand(abc.ABC):
    """Abstract base class for all migration commands.

    Defines the interface that all migration commands must implement.
    A migration command is an operation to be executed in a MongoDB database.
    """

    __slots__ = ()

    @abc.abstractmethod
    def execute(self, conn: pymongo.MongoClient[typing.Dict[str, typing.Any]]) -> None:
        """Execute the migration command on the given MongoClient object.

        Parameters
        ----------
        conn : MongoClient[typing.Dict[str, typing.Any]]
            A MongoClient object representing the connection to the MongoDB database.
        """
        ...
