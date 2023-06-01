from __future__ import annotations

import enum
import logging
import logging.config
import os
import typing

if typing.TYPE_CHECKING:
    from mongorunway import mongo
    from mongorunway.application import config

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
