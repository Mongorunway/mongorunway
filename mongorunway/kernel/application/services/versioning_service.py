from __future__ import annotations

__all__: typing.Sequence[str] = (
    "version2position",
    "position2version",
    "get_upgrading_version",
    "get_downgrading_version",
)

import typing

if typing.TYPE_CHECKING:
    from mongorunway.kernel.application.ui import MigrationUI


def get_downgrading_version(application: MigrationUI, /) -> typing.Optional[int]:
    downgrading_to = application.applied.acquire_latest_migration()
    if downgrading_to is not None:
        downgrading_to = downgrading_to.version - 1

    return downgrading_to or None


def get_upgrading_version(application: MigrationUI, /) -> typing.Optional[int]:
    upgrading_to = application.applied.acquire_latest_migration()
    if upgrading_to is not None:
        upgrading_to = upgrading_to.version

    return upgrading_to


def version2position(application: MigrationUI, migration_version: int, /) -> int:
    if migration_version < (start := application.config.invariants.versioning_starts_from):
        raise ValueError("Version cannot be less than start value.")

    return migration_version - start


def position2version(application: MigrationUI, migration_position: int, /) -> int:
    # Only when naming guarantees a clear version order
    return migration_position + application.config.invariants.versioning_starts_from
