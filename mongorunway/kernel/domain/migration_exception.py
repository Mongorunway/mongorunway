from __future__ import annotations

__all__: typing.Sequence[str] = (
    "MigrationError",
    "MigrationFailedError",
    "MigrationTransactionFailedError",
    "NothingToUpgradeError",
    "NothingToDowngradeError",
    "MigrationHookError",
    "MigrationFileChangedError",
)

import typing


class MigrationError(Exception):
    __slots__: typing.Sequence[str] = ()

    pass


class MigrationFailedError(MigrationError):
    __slots__: typing.Sequence[str] = ()

    pass


class MigrationTransactionFailedError(MigrationFailedError):
    __slots__: typing.Sequence[str] = ()

    pass


class NothingToUpgradeError(MigrationFailedError):
    __slots__: typing.Sequence[str] = ()

    pass


class NothingToDowngradeError(MigrationFailedError):
    __slots__: typing.Sequence[str] = ()

    pass


class MigrationHookError(MigrationError):
    __slots__: typing.Sequence[str] = ()

    pass


class MigrationFileChangedError(MigrationHookError):
    __slots__: typing.Sequence[str] = ()

    pass