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
"""Module contains interfaces for hooks used in a migration application."""
from __future__ import annotations

__all__: typing.Sequence[str] = (
    "MigrationHook",
    "PrioritizedMigrationHook",
)

import abc
import typing

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.ui import MigrationUI


class MigrationHook(abc.ABC):
    """Abstract base class for defining hooks for migration application."""

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def apply(self, application: MigrationUI, /) -> None:
        """Applies the hook to the migration application.

        Parameters
        ----------
        application: MigrationUI
            The migration application to apply the hook to.
        """
        ...


class PrioritizedMigrationHook(abc.ABC):
    """Abstract base class for a prioritized migration hook.

    A prioritized migration hook is a wrapper around a `MigrationHook` that allows defining
    a priority level for the hook.

    Notes
    -----
    The hooks with higher priority level will be executed first during the migration process.
    """

    __slots__: typing.Sequence[str] = ()

    @abc.abstractmethod
    def __eq__(self, other: typing.Any) -> bool:
        """Method for determining the equality of two objects.

        Parameters
        ----------
        other : typing.Any
            Another object with which the current object is being compared.

        Returns
        -------
        bool
            Returns True if the current object is equivalent to the other object,
            False otherwise.
        """
        ...

    @abc.abstractmethod
    def __hash__(self) -> int:
        """Method for determining the hash value of an object.

        Returns
        -------
        int
            The hash value of the object.
        """
        ...

    @property
    @abc.abstractmethod
    def priority(self) -> int:
        """Property for getting the priority of an object.

        Returns
        -------
        int
            The priority value of the object.
        """
        ...

    @property
    @abc.abstractmethod
    def item(self) -> MigrationHook:
        """Property for getting the migration hook item.

        Returns
        -------
        MigrationHook
            The migration hook object.
        """
        ...
