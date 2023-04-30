from __future__ import annotations

__all__: typing.Sequence[str] = (
    "calculate_migration_checksum",
)

import hashlib
import typing

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration_module import MigrationModule


def calculate_migration_checksum(module: MigrationModule, /) -> str:
    with open(module.location, "r") as f:
        file_data = f.read().encode()
        return hashlib.md5(file_data).hexdigest()
