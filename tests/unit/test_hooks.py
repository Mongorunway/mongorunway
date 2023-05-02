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

from unittest.mock import Mock

from mongorunway.kernel.infrastructure.hooks import PrioritizedHook


def test_prioritized_hook_priority() -> None:
    ph = PrioritizedHook(1, Mock())
    assert ph.priority == 1


def test_prioritized_hook_item() -> None:
    mh = Mock()
    ph = PrioritizedHook(1, mh)
    assert ph.item == mh


def test_prioritized_hook_order() -> None:
    ph1 = PrioritizedHook(1, Mock())
    ph2 = PrioritizedHook(2, Mock())
    assert ph1 < ph2
    assert ph2 > ph1
    assert ph1 <= ph2
    assert ph2 >= ph1
    assert ph1 != ph2


def test_prioritized_hook_hash() -> None:
    ph1 = PrioritizedHook(1, Mock())
    ph2 = PrioritizedHook(1, Mock())
    ph3 = PrioritizedHook(2, Mock())
    assert hash(ph1) == hash(ph2)
    assert hash(ph1) != hash(ph3)
