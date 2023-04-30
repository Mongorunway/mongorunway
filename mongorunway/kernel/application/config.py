from __future__ import annotations

__all__: typing.Sequence[str] = (
    "migration_file_template",
    "AuditlogConfig",
    "RuntimeConfig",
    "ConnectionConfig",
    "StartupConfig",
    "InvariantsConfig",
    "ApplicationConfig",
    "LoggingConfig",
)

import configparser
import dataclasses
import logging
import string
import typing

import pymongo

from mongorunway.kernel import util
from mongorunway.kernel.application.ports.filename_strategy import FilenameStrategy

T = typing.TypeVar("T")
StoreT = typing.TypeVar("StoreT")

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("mongorunway.config")

migration_file_template = string.Template(
    """\
from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from mongorunway import MigrationCommand

version = $version


def upgrade() -> typing.Iterable[MigrationCommand]:
    return $upgrade_commands


def downgrade() -> typing.Iterable[MigrationCommand]:
    return $downgrade_commands
"""
)


@dataclasses.dataclass(frozen=True)
class InvariantsConfig:
    versioning_starts_from: int = 1


@dataclasses.dataclass
class ConnectionConfig:
    mongo_client: pymongo.MongoClient[typing.Dict[str, typing.Any]]
    mongo_database: pymongo.collection.Database[typing.Dict[str, typing.Any]]
    applied_migration_collection: pymongo.collection.Collection[typing.Dict[str, typing.Any]]
    pending_migration_collection: pymongo.collection.Collection[typing.Dict[str, typing.Any]]

    @classmethod
    def from_parser(
        cls, parser: configparser.ConfigParser, *, application_name: str, con_extras: typing.Any,
    ) -> ConnectionConfig:
        section = "app" + "_" + application_name
        client_args = [parser.get(section, "uri")]

        if (mongo_port := parser.getint(section, "port", fallback=None)) is not None:
            client_args.append(mongo_port)

        client = pymongo.MongoClient(
            *client_args,
            **{
                "username": parser.get(section, "username", fallback=None),
                "password": parser.get(section, "password", fallback=None),
            },
            **con_extras,
        )

        database = client.get_database(parser.get(section, "database"))

        return ConnectionConfig(
            mongo_client=client,
            mongo_database=database,
            applied_migration_collection=database.get_collection(
                parser.get(section, "collection_applied")
            ),
            pending_migration_collection=database.get_collection(
                parser.get(section, "collection_pending"),
            ),
        )


@dataclasses.dataclass
class StartupConfig:
    sync_scripts_with_queues: bool
    recalculate_migrations_checksum: bool
    raise_if_migrations_checksum_mismatch: bool

    @classmethod
    def from_parser(cls, parser: configparser.ConfigParser, *, application_name: str) -> StartupConfig:
        startup_section = "app" + "_" + application_name + "." + "on_startup"
        return StartupConfig(
            raise_if_migrations_checksum_mismatch=parser.getboolean(
                startup_section,
                "raise_if_migrations_checksum_mismatch",
                fallback=True,
            ),
            sync_scripts_with_queues=parser.getboolean(
                startup_section,
                "sync_scripts_with_queues",
                fallback=True,
            ),
            recalculate_migrations_checksum=parser.getboolean(
                startup_section,
                "recalculate_migrations_checksum",
                fallback=False,
            ),
        )


@dataclasses.dataclass
class RuntimeConfig:
    filename_strategy: FilenameStrategy
    strict_naming: bool
    raise_if_nothing_happens: bool

    @classmethod
    def from_parser(cls, parser: configparser.ConfigParser) -> RuntimeConfig:
        section = "runtime"
        try:
            filename_strategy_path = parser.get(section, "filename_strategy").replace("\n", "")
            filename_strategy_class = util.import_class_from_module(
                filename_strategy_path,
                cast=FilenameStrategy,
            )

        except (configparser.NoSectionError, ImportError, AttributeError):
            filename_strategy_class = util.import_class_from_module(
                "mongorunway.kernel.infrastructure.filename_strategies.NumericalFilenameStrategy",
                cast=FilenameStrategy,
            )

        return RuntimeConfig(
            strict_naming=parser.getboolean(section, "strict_naming", fallback=True),
            filename_strategy=filename_strategy_class(),
            raise_if_nothing_happens=parser.getboolean(
                section,
                "raise_if_nothing_happens",
                fallback=True,
            ),
        )


@dataclasses.dataclass
class AuditlogConfig:
    auditlog_collection: typing.Optional[pymongo.collection.Collection[typing.Dict[str, typing.Any]]]

    @classmethod
    def from_parser(
        cls, parser: configparser.ConfigParser, *, application_name: str, connection_config: ConnectionConfig,
    ) -> AuditlogConfig:
        section = "app" + "_" + application_name + "." + "auditlog"
        try:
            target_collection = connection_config.mongo_database.get_collection(
                parser.get(section, "collection_auditlog"),
            )
        except configparser.NoSectionError:
            target_collection = None

        return AuditlogConfig(
            auditlog_collection=target_collection,
        )


@dataclasses.dataclass
class LoggingConfig:
    level: int

    @classmethod
    def from_parser(cls, parser: configparser.ConfigParser) -> LoggingConfig:
        section = "log"
        return cls(
            level=parser.get(section, "level", fallback=logging.INFO),
        )


@dataclasses.dataclass
class ApplicationConfig:
    name: str
    migration_scripts_dir: str
    connection: ConnectionConfig
    on_startup: StartupConfig
    runtime: RuntimeConfig
    auditlog: AuditlogConfig
    invariants: InvariantsConfig
    log: LoggingConfig

    @classmethod
    def from_ini_file(
        cls,
        filepath: str,
        *,
        name: str,
        con_extras: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    ) -> ApplicationConfig:
        parser = configparser.ConfigParser()
        parser.read(filepath)
        return cls.from_parser(parser, name=name, con_extras=con_extras)

    @classmethod
    def from_dict(
        cls,
        mapping: typing.Mapping[str, typing.Any],
        *,
        name: str,
        con_extras: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    ) -> ApplicationConfig:
        parser = configparser.ConfigParser()
        parser.read_dict(mapping)
        return cls.from_parser(parser, name=name, con_extras=con_extras)

    @classmethod
    def from_parser(
        cls,
        parser: configparser.ConfigParser,
        *,
        name: str,
        con_extras: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    ) -> ApplicationConfig:
        root_section = "root"
        if con_extras is None:
            con_extras = {}

        for section in parser.sections():
            if section.startswith("app"):
                # maxsplit=1 for 'app_root.sections_with_underscores' sections.
                _, app_name = section.split("_", maxsplit=1)
                if app_name == name:
                    return cls(
                        name=name,
                        invariants=InvariantsConfig(),
                        log=LoggingConfig.from_parser(parser),
                        runtime=RuntimeConfig.from_parser(parser),
                        migration_scripts_dir=parser.get(root_section, "scripts_dir"),
                        on_startup=StartupConfig.from_parser(parser, application_name=app_name),
                        connection=(
                            con_cfg := ConnectionConfig.from_parser(
                                parser,
                                application_name=app_name,
                                con_extras=con_extras,
                            )
                        ),
                        auditlog=AuditlogConfig.from_parser(
                            parser,
                            application_name=app_name,
                            connection_config=con_cfg,
                        ),
                    )

        raise ValueError(
            f"Application section {('app_' + name)!r} is not found."
        )
