from __future__ import annotations

import logging
import logging.config
import os
import typing

if typing.TYPE_CHECKING:
    from mongorunway.application import config

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("mongorunway.ux")
_VALIDATOR: typing.Final[typing.Dict[str, typing.Any]] = {
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
            "_id": {"bsonType": "int"},
            "name": {"bsonType": "string", "minLength": 1},
            "version": {"bsonType": "int", "minimum": 1},
            "checksum": {"bsonType": "string"},
            "is_applied": {"bsonType": "bool"},
            "description": {"bsonType": "string"},
        },
    }
}
_APPLIED_INDEX = [("is_applied", 1), ("_id", -1)]
_PENDING_INDEX = [("is_applied", 1)]


def init_logging(configuration: config.Config, /) -> None:
    if configuration.application.is_logged():
        if _LOGGER.isEnabledFor(logging.INFO):
            _LOGGER.info("Mongorunway loggers are already configured, skipping...")
        else:
            logging.config.fileConfig(configuration.filesystem.config_dir)
            _LOGGER.info("Mongorunway loggers successfully configured.")


def init_migration_directory(configuration: config.Config, /) -> None:
    _LOGGER.info("Checking if the migration directory exists...")
    scripts_dir = configuration.filesystem.scripts_dir

    if not os.path.exists(scripts_dir):
        _LOGGER.info("The migration directory was not found, resolving...")
        os.mkdir(scripts_dir)
        _LOGGER.info(
            "The migration directory has been successfully created at %s",
            scripts_dir,
        )
    else:
        _LOGGER.info("Migration directory is already exists, skipping...")


def init_migration_collection(configuration: config.Config, /) -> None:
    default_collection_name = "migrations"

    if (
        default_collection_name
        not in (database := configuration.application.app_database).list_collection_names()
    ):
        _LOGGER.info("Collection %s is not found, resolving...", default_collection_name)

        kwargs: typing.Dict[str, typing.Any] = {}
        if configuration.application.use_schema_validation:
            _LOGGER.info(
                "Applying a validator to %s collection...",
                default_collection_name,
            )
            kwargs["validator"] = _VALIDATOR

        database.create_collection(
            default_collection_name,
            **kwargs,
        )

        _LOGGER.info("Migrations collection successfully configured.")
    else:
        _LOGGER.info("Migration collection is already exists, skipping...")


def init_migration_indexes(configuration: config.Config, /) -> None:
    collection = configuration.application.app_migrations_collection

    if configuration.application.use_indexing:
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

        _create_index_if_not_exists(_APPLIED_INDEX)
        _create_index_if_not_exists(_PENDING_INDEX)


def drop_migration_indexes(configuration: config.Config, /) -> None:
    collection = configuration.application.app_migrations_collection

    if not configuration.application.use_indexing:
        _LOGGER.info(
            "The 'use_indexes' parameter is set to False, checking the indexes that "
            "need to be deleted...",
        )

        indexes = collection.index_information()

        def _drop_index_if_exists(index: typing.Sequence[typing.Tuple[str, int]]) -> None:
            translated_index = "_".join(f"{x}_{y}" for x, y in [_ for _ in index])

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

        _drop_index_if_exists(_APPLIED_INDEX)
        _drop_index_if_exists(_PENDING_INDEX)


def configure_migration_indexes(configuration: config.Config, /) -> None:
    if configuration.application.use_indexing:
        init_migration_indexes(configuration)
        return

    drop_migration_indexes(configuration)
