from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from mongorunway.application import config
    from mongorunway.domain import migration as domain_migration


def get_migration_file_path(
    migration: domain_migration.Migration,
    configuration: config.Config,
) -> str:
    filename = configuration.filesystem.filename_strategy.transform_migration_filename(
        migration.name,
        migration.version,
    )
    return configuration.filesystem.scripts_dir + "\\" + filename + ".py"
