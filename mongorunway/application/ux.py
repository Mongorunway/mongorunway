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

__all__: typing.Sequence[str] = (
    "MIGRATION_SCHEMA_VALIDATOR",
    "PENDING_MIGRATION_INDEX",
    "APPLIED_MIGRATION_INDEX",
    "ValidationAction",
    "ValidationLevel",
    "configure_logging",
    "configure_migration_indexes",
    "configure_migration_directory",
    "configure_migration_collection",
    "configure_migration_schema_validators",
    "init_components",
    "init_logging",
    "init_migration_indexes",
    "init_schema_validators",
    "init_migration_collection",
    "init_migration_directory",
    "remove_migration_indexes",
    "remove_migration_schema_validators",
    "sync_scripts_with_repository",
)

import enum
import logging
import logging.config
import os
import typing

from mongorunway.application.services import migration_service

if typing.TYPE_CHECKING:
    from mongorunway import mongo
    from mongorunway.application import config
    from mongorunway.application import traits

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("mongorunway.ux")

MIGRATION_SCHEMA_VALIDATOR: typing.Final[typing.Dict[str, typing.Any]] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "_id",
            "name",
            "version",
            "checksum",
            "is_applied",
            "description",
        ],
        "properties": {
            "_id": {
                "bsonType": "int",
            },
            "name": {
                "bsonType": "string",
                "minLength": 1,
            },
            "version": {
                "bsonType": "int",
                "minimum": 1,
            },
            "checksum": {
                "bsonType": "string",
            },
            "is_applied": {
                "bsonType": "bool",
            },
            "description": {
                "bsonType": "string",
            },
        },
    }
}

APPLIED_MIGRATION_INDEX: typing.Final[typing.Sequence[typing.Tuple[str, int]]] = [
    ("is_applied", 1),
    ("_id", -1),
]

PENDING_MIGRATION_INDEX: typing.Final[typing.Sequence[typing.Tuple[str, int]]] = [
    ("is_applied", 1),
]


def configure_logging(config_dict: typing.Dict[str, typing.Any]) -> None:
    if _LOGGER.isEnabledFor(logging.INFO):
        _LOGGER.info("Mongorunway loggers are already configured, skipping...")
    else:
        logging.config.dictConfig(config_dict)
        _LOGGER.info("Mongorunway loggers successfully configured.")


def configure_migration_directory(scripts_dir: str) -> None:
    _LOGGER.info("Checking if the migration directory exists...")
    if not os.path.exists(scripts_dir):
        _LOGGER.info("The migration directory was not found, resolving...")
        os.mkdir(scripts_dir)
        _LOGGER.info(
            "The migration directory has been successfully created at %s",
            scripts_dir,
        )
    else:
        _LOGGER.info("Migration directory is already exists, skipping...")


def configure_migration_collection(
    database: mongo.Database,
    use_schema_validation: bool,
    collection_name: str = "migrations",
) -> None:
    if collection_name not in database.list_collection_names():
        _LOGGER.info("Collection %s is not found, resolving...", collection_name)

        kwargs: typing.Dict[str, typing.Any] = {}
        if use_schema_validation:
            _LOGGER.info(
                "Applying a validator to %s collection...",
                collection_name,
            )
            kwargs["validator"] = MIGRATION_SCHEMA_VALIDATOR

        database.create_collection(
            collection_name,
            **kwargs,
        )

        _LOGGER.info("Migrations collection successfully configured.")
    else:
        _LOGGER.info("Migration collection is already exists, skipping...")


def configure_migration_indexes(collection: mongo.Collection) -> None:
    _LOGGER.info("The 'use_indexes' parameter is set to True, checking for missing indexes...")

    indexes = collection.index_information()

    def _create_index_if_not_exists(index: typing.Sequence[typing.Tuple[str, int]]) -> None:
        translated_index = "_".join(f"{x}_{y}" for x, y in [_ for _ in index])

        if translated_index not in indexes:
            _LOGGER.info(
                "Found one missing index: %s, resolving...",
                translated_index,
            )
            collection.create_index(index)
            _LOGGER.info("Index %s successfully configured.", translated_index)
        else:
            _LOGGER.info(
                "Index %s is already configured, skipping...",
                translated_index,
            )

    _create_index_if_not_exists(APPLIED_MIGRATION_INDEX)
    _create_index_if_not_exists(PENDING_MIGRATION_INDEX)


def remove_migration_indexes(collection: mongo.Collection) -> None:
    _LOGGER.info(
        "The 'use_indexes' parameter is set to False, checking the indexes that "
        "need to be deleted...",
    )

    indexes = collection.index_information()

    def _drop_index_if_exists(index: typing.Sequence[typing.Tuple[str, int]]) -> None:
        translated_index = mongo.translate_index(index)

        if translated_index in indexes:
            _LOGGER.info(
                "Found one existing index: %s, dropping...",
                translated_index,
            )
            collection.drop_index(index)
            _LOGGER.info("Index %s successfully dropped.", translated_index)
        else:
            _LOGGER.info(
                "Index %s is already dropped, skipping...",
                translated_index,
            )

    _drop_index_if_exists(APPLIED_MIGRATION_INDEX)
    _drop_index_if_exists(PENDING_MIGRATION_INDEX)


def configure_migration_schema_validators(collection: mongo.Collection) -> None:
    validator = collection.options().get("validator")
    _LOGGER.info("Schema validation is enabled, checking for validators...")

    if validator != MIGRATION_SCHEMA_VALIDATOR:
        _LOGGER.info("Undefined validator found, removing...")

    collection.database.command(
        "collMod",
        collection.name,
        validationLevel=ValidationLevel.STRICT,
        validationAction=ValidationAction.ERROR,
        validator=MIGRATION_SCHEMA_VALIDATOR,
    )

    _LOGGER.info("Mongorunway migrations schema validator successfully configured.")


def remove_migration_schema_validators(collection: mongo.Collection) -> None:
    validator = collection.options().get("validator")
    _LOGGER.info("Schema validation is disabled, checking for validators...")
    if validator == MIGRATION_SCHEMA_VALIDATOR:
        collection.database.command(
            "collMod",
            collection.name,
            validator={},
        )
        _LOGGER.info("Mongorunway schema validator successfully removed.")


# HIGH-LEVEL UX TOOLS


def sync_scripts_with_repository(
    application: traits.MigrationSessionAware,
) -> typing.Sequence[str]:
    synced = []
    service = migration_service.MigrationService(application.session)
    for migration in service.get_migrations():
        if not application.session.has_migration(migration):
            application.session.append_migration(migration)
            synced.append(migration.name)

            _LOGGER.info(
                "%s: migration '%s' with version %s was synced"
                " "
                "and successfully append to pending.",
                sync_scripts_with_repository.__name__,
                migration.name,
                migration.version,
            )

    return synced


def init_logging(configuration: config.Config, /) -> None:
    if configuration.application.is_logged:
        configure_logging(configuration.logging_dict)


def init_components(configuration: config.Config, /) -> None:
    journal = configuration.application.app_auditlog_journal
    if journal is not None:
        journal.set_max_records(configuration.application.app_auditlog_limit)


def init_migration_directory(configuration: config.Config, /) -> None:
    configure_migration_directory(configuration.filesystem.scripts_dir)


def init_migration_collection(configuration: config.Config, /) -> None:
    configure_migration_collection(
        database=configuration.application.app_database,
        use_schema_validation=configuration.application.use_schema_validation,
    )


def init_migration_indexes(configuration: config.Config, collection: mongo.Collection) -> None:
    if configuration.application.use_indexing:
        configure_migration_indexes(collection)
    else:
        remove_migration_indexes(collection)


def init_schema_validators(configuration: config.Config, collection: mongo.Collection) -> None:
    if configuration.application.use_schema_validation:
        configure_migration_schema_validators(collection)
    else:
        remove_migration_schema_validators(collection)


class ValidationAction(str, enum.Enum):
    ERROR = "error"
    WARNING = "warn"


class ValidationLevel(str, enum.Enum):
    OFF = "off"
    STRICT = "strict"
    MODERATE = "moderate"
