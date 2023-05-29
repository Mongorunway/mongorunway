from __future__ import annotations

__all__: typing.Sequence[str] = (
    "migration_file_template",
    "MigrationService",
)

import os
import string
import typing

from mongorunway import util
from mongorunway.application import config
from mongorunway.application.services import checksum_service
from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_module as domain_module

if typing.TYPE_CHECKING:
    from mongorunway.application import session

migration_file_template = string.Template(
    """\
from __future__ import annotations

import typing

import mongorunway

version = $version


@mongorunway.migration
def upgrade() -> typing.Sequence[mongorunway.MigrationCommand]:
    return $upgrade_commands


@mongorunway.migration
def downgrade() -> typing.Sequence[mongorunway.MigrationCommand]:
    return $downgrade_commands
"""
)


class MigrationService:
    def __init__(self, app_session: session.MigrationSession) -> None:
        self._session = app_session

    def get_migration(self, migration_name: str) -> domain_migration.Migration:
        module = util.get_module(
            self._session.session_config.filesystem.scripts_dir, migration_name
        )
        migration_module = domain_module.MigrationModule(module)

        model = self._session.get_migration_model_by_version(module.version)

        migration = domain_migration.Migration(
            name=migration_module.get_name(),
            version=module.version,
            description=migration_module.description,
            checksum=checksum_service.calculate_migration_checksum(migration_module),
            downgrade_process=migration_module.downgrade_process,
            upgrade_process=migration_module.upgrade_process,
            is_applied=False if model is None else model.is_applied,
        )

        return migration

    @typing.no_type_check
    def get_migrations(self) -> typing.Sequence[domain_migration.Migration]:
        directory = self._session.session_config.filesystem.scripts_dir
        filename_strategy = self._session.session_config.filesystem.filename_strategy

        if self._session.session_config.filesystem.strict_naming:
            # All migrations are in the correct order by name.
            return [
                self.get_migration(
                    filename_strategy.transform_migration_filename(migration_name, position),
                )
                for position, migration_name in enumerate(
                    sorted(os.listdir(directory)),
                    config.VERSIONING_STARTS_FROM,
                )
                if util.is_valid_filename(directory, migration_name)
            ]

        else:
            migrations: typing.Dict[int, domain_migration.Migration] = {}
            for migration_name in sorted(os.listdir(directory)):
                if not util.is_valid_filename(directory, migration_name):
                    continue

                module = util.get_module(directory, migration_name)
                try:
                    migration_version = module.version
                except AttributeError:
                    raise ImportError(
                        f"Migration {migration_name} in non-strict mode must have "
                        f"'version' variable."
                    )

                migrations[migration_version] = self.get_migration(
                    migration_name,
                )

            if (start := config.VERSIONING_STARTS_FROM) not in migrations:
                # ...
                raise ValueError(f"Versioning starts from {start}.")

            return [migrations[key] for key in sorted(migrations.keys())]

    def create_migration_file_template(
        self,
        migration_filename: str,
        migration_version: typing.Optional[int] = None,
    ) -> None:
        if migration_version is None:
            migration_version = len(self.get_migrations()) + 1

        if self._session.has_migration_with_version(migration_version):
            raise ValueError(f"Migration with version {migration_version} already exist.")

        current_version = self._session.get_current_version() or 0
        if (migration_version - current_version) > 1:
            raise ValueError(
                f"Versions of migrations must be consistent: the next version "
                f"must be {current_version + 1!r}, but {migration_version!r} received."
            )

        filename_strategy = self._session.session_config.filesystem.filename_strategy
        if self._session.session_config.filesystem.strict_naming:
            migration_filename = filename_strategy.transform_migration_filename(
                migration_filename,
                migration_version,
            )

            if not migration_filename.endswith(".py"):
                migration_filename += ".py"

        with open(
            os.path.join(
                self._session.session_config.filesystem.scripts_dir,
                migration_filename,
            ),
            "w",
        ) as file:
            file.write(
                migration_file_template.safe_substitute(
                    version=migration_version,
                    upgrade_commands=[],
                    downgrade_commands=[],
                )
            )

    def validate_migration_file(self, migration_filename: str) -> bool:
        pass
