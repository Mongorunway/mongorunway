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
from unittest.mock import Mock

import pytest
import pymongo

from mongorunway.kernel.persistence.queues import (
    BaseMigrationQueue,
    AppliedMigrationQueue,
    PendingMigrationQueue,
)
from mongorunway.kernel.application.ports.queue import MigrationQueue


@pytest.mark.parametrize(
    "queue, queue_sort_order",
    [
        (
            BaseMigrationQueue(
                application=Mock(),
                collection=Mock(),
                sort_order=1,
            ),
            1,
        ),
        (
            AppliedMigrationQueue(
                application=Mock(),
            ),
            pymongo.DESCENDING,  # FIFO
        ),
        (
            PendingMigrationQueue(
                application=Mock(),
            ),
            pymongo.ASCENDING,  # LIFO
        ),
    ],
)
def test_queues(queue: MigrationQueue, queue_sort_order: int) -> None:
    queue_type = type(queue)

    assert issubclass(queue_type, MigrationQueue)
    assert issubclass(queue_type, collections.abc.Sized)
    assert issubclass(queue_type, collections.abc.Container)

    assert queue.sort_order == queue_sort_order
