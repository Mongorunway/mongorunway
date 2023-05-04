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
"""Module that contains the configuration for the migration application.
This module provides the settings used by the migration application.
"""
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
"""
This constant migration_file_template is a string template that specifies the structure 
of a migration file in the Mongorunway application. It contains placeholders for the 
migration's version number, upgrade commands, and downgrade commands.

The string.Template class is used to construct the template, and the placeholders in 
the template are denoted by $ followed by the name of the placeholder.

This constant is used to generate new migration files in the application. The placeholders 
in the template are filled with the appropriate values when a new migration is created, 
and the resulting string is saved as the migration file.
"""


@dataclasses.dataclass(frozen=True)
class InvariantsConfig:
    """The InvariantsConfig class is a dataclass that represents the configuration for the
    invariants of a migration. It is used to specify the starting version for migration versions.

    Parameters
    ----------
    versioning_starts_from : int
        The version number to start versioning migrations from. The default value is 1.

    Notes
    -----
    This class is marked as `frozen`, which means that once an object of this class is created, its
    attributes cannot be modified. It is typically used as a value object that holds the configuration
    for the application.
    """

    versioning_starts_from: int = 1
    """The version number to start versioning migrations from. The default value is 1."""


@dataclasses.dataclass
class ConnectionConfig:
    """This class represents the configuration for the MongoDB connection and collections required
    for migration management.

    Parameters
    ----------
    mongo_client : MongoClient[Dict[str, Any]]
        A pymongo.MongoClient instance that represents the MongoDB client to connect to.
    mongo_database : Database[Dict[str, Any]]
        A pymongo.database.Database instance that represents the MongoDB database to use.
    applied_migration_collection : Collection[Dict[str, Any]]
        A pymongo.collection.Collection instance that represents the MongoDB collection used to store
        the applied migrations.
    pending_migration_collection : Collection[Dict[str, Any]]
        A pymongo.collection.Collection instance that represents the MongoDB collection used to store
        the pending migrations.
    """

    mongo_client: pymongo.MongoClient[typing.Dict[str, typing.Any]]
    """A pymongo.MongoClient instance that represents the MongoDB client to connect to."""

    mongo_database: pymongo.collection.Database[typing.Dict[str, typing.Any]]
    """A pymongo.database.Database instance that represents the MongoDB database to use."""

    applied_migration_collection: pymongo.collection.Collection[typing.Dict[str, typing.Any]]
    """A pymongo.collection.Collection instance that represents the MongoDB collection used to store 
    the applied migrations.
    """

    pending_migration_collection: pymongo.collection.Collection[typing.Dict[str, typing.Any]]
    """A pymongo.collection.Collection instance that represents the MongoDB collection used to store 
    the pending migrations.
    """

    @classmethod
    def from_parser(
        cls,
        parser: configparser.ConfigParser,
        *,
        application_name: str,
        con_extras: typing.Mapping[str, typing.Any],
    ) -> ConnectionConfig:
        """Create a ConnectionConfig object from a ConfigParser object.

        Parameters
        ----------
        parser : ConfigParser
            The ConfigParser object containing the necessary configuration options.
        application_name : str
            The name of the application to connect to.
        con_extras : Mapping[str, Any]
            Additional keyword arguments to pass to pymongo.MongoClient.

        Returns
        -------
        ConnectionConfig
            The ConnectionConfig object containing the necessary connections and collections.
        """
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
    """The StartupConfig class represents a configuration for startup options.

    Parameters
    ----------
    sync_scripts_with_queues : bool
        A boolean value indicating whether the migration scripts should be synchronized with
        the queues. If True, the scripts are added to the queue, otherwise they are not added.
    recalculate_migrations_checksum : bool
        A boolean value indicating whether the checksum of the migrations should be recalculated.
        If True, the checksum is recalculated, otherwise the previous value is used.
    raise_if_migrations_checksum_mismatch : bool
        A boolean value indicating whether to raise an exception if there is a checksum mismatch.
        If True, an exception is raised, otherwise it is not.
    """

    sync_scripts_with_queues: bool
    """A boolean value indicating whether the migration scripts should be synchronized with 
    the queues. If True, the scripts are added to the queue, otherwise they are not added.
    """

    recalculate_migrations_checksum: bool
    """A boolean value indicating whether the checksum of the migrations should be recalculated. 
    If True, the checksum is recalculated, otherwise the previous value is used.
    """

    raise_if_migrations_checksum_mismatch: bool
    """A boolean value indicating whether to raise an exception if there is a checksum mismatch. 
    If True, an exception is raised, otherwise it is not. 
    """

    @classmethod
    def from_parser(cls, parser: configparser.ConfigParser, *, application_name: str) -> StartupConfig:
        """Create a StartupConfig instance from a configparser.ConfigParser instance.

        Parameters
        ----------
        parser : ConfigParser
            A ConfigParser instance containing startup configuration settings.
        application_name : str
            The name of the application.

        Returns
        -------
        StartupConfig
            A StartupConfig instance created from the parser.
        """
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
    """Configuration class for runtime options.

    Parameters
    ----------
    filename_strategy : FilenameStrategy
        A strategy object to generate filenames.
    strict_naming : bool
        If set to True, will enforce strict naming conventions for migration files.
    raise_if_nothing_happens : bool
        If set to True, will raise an error if no migration is needed to be applied.
    """

    filename_strategy: FilenameStrategy
    """A strategy object to generate filenames."""

    strict_naming: bool
    """If set to True, will enforce strict naming conventions for migration files."""

    raise_if_nothing_happens: bool
    """If set to True, will raise an error if no migration is needed to be applied."""

    @classmethod
    def from_parser(cls, parser: configparser.ConfigParser) -> RuntimeConfig:
        """Create a new instance of `RuntimeConfig` from a given `ConfigParser` object.

        Parameters
        ----------
        parser : ConfigParser
            The configuration parser.

        Returns
        -------
        RuntimeConfig
            A new instance of `RuntimeConfig`.
        """
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
    """This is a dataclass representing the configuration of the audit log for a MongoRunway application.

    auditlog_collection : Optional[Collection[Dict[str, Any]]]
        An optional instance of a pymongo.collection.Collection object representing the collection in
        which audit log entries should be stored. If not provided, audit logging will be disabled.
    """

    auditlog_collection: typing.Optional[pymongo.collection.Collection[typing.Dict[str, typing.Any]]]
    """An optional instance of a pymongo.collection.Collection object representing the collection in 
    which audit log entries should be stored. If not provided, audit logging will be disabled.
    """

    @classmethod
    def from_parser(
        cls, parser: configparser.ConfigParser, *, application_name: str, connection_config: ConnectionConfig,
    ) -> AuditlogConfig:
        """Create a new instance of `AuditlogConfig` from a given `configparser.ConfigParser` object.

        Parameters
        ----------
        parser : ConfigParser
            A ConfigParser object containing the configuration of the application.
        application_name : str
            The name of the application.
        connection_config : ConnectionConfig
            A ConnectionConfig object containing the configuration of the MongoDB connection.

        Returns
        -------
        AuditlogConfig
            An AuditlogConfig object containing the configuration of the auditlog collection, or None
            if the collection name is not found.
        """
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
    """A dataclass representing logging configuration.

    Attributes
    ----------
    level : int
        The logging level to use.
    """

    level: int
    """he logging level to use."""

    @classmethod
    def from_parser(cls, parser: configparser.ConfigParser) -> LoggingConfig:
        """Returns an instance of LoggingConfig created from a ConfigParser object.

        Parameters
        ----------
        parser : ConfigParser
            The ConfigParser object to use for creating the LoggingConfig instance.

        Returns
        -------
        LoggingConfig
            An instance of LoggingConfig.
        """
        section = "log"

        return cls(
            level=getattr(logging, parser.get(section, "level", fallback="INFO"), logging.INFO),
        )


@dataclasses.dataclass
class ApplicationConfig:
    """Data class that represents the configuration for a single application.

    Parameters
    ----------
    name : str
        The name of the application.
    migration_scripts_dir : str
        The directory containing the application's migration scripts.
    connection : ConnectionConfig
        The configuration for the database connection.
    on_startup : StartupConfig
        The configuration for the application's startup behavior.
    runtime : RuntimeConfig
        The runtime configuration for the application.
    auditlog : AuditlogConfig
        The configuration for the auditlog.
    invariants : InvariantsConfig
        The configuration for the application's invariants.
    log : LoggingConfig
        The configuration for the logging behavior.
    """

    name: str
    """The name of the application."""

    migration_scripts_dir: str
    """The directory containing the application's migration scripts."""

    connection: ConnectionConfig
    """The configuration for the database connection."""

    on_startup: StartupConfig
    """The configuration for the application's startup behavior."""

    runtime: RuntimeConfig
    """The runtime configuration for the application."""

    auditlog: AuditlogConfig
    """The configuration for the auditlog."""

    invariants: InvariantsConfig
    """The configuration for the application's invariants."""

    log: LoggingConfig
    """The configuration for the logging behavior."""

    @classmethod
    def from_ini_file(
        cls,
        filepath: str,
        *,
        name: str,
        con_extras: typing.Optional[typing.Mapping[str, typing.Any]] = None,
    ) -> ApplicationConfig:
        """Reads the configuration values from the specified INI file and creates an
        `ApplicationConfig` object.

        Parameters
        ----------
        filepath : str
            The path to the INI file to read.
        name : str
            The name of the application.
        con_extras : Mapping[str, Any], optional
            Optional additional connection parameters.

        Returns
        -------
        ApplicationConfig
            The `ApplicationConfig` object created from the configuration values in the INI file.
        """
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
        """Return an ApplicationConfig instance constructed from a dictionary.

        Parameters
        ----------
        mapping : Mapping[str, Any]
            A dictionary-like object containing key-value pairs to parse and convert to an
            ApplicationConfig object.
        name : str
            The name of the application.
        con_extras : Mapping[str, Any], optional
            Optional extra arguments to be passed to the ConnectionConfig constructor, by
            default None.

        Returns
        -------
        ApplicationConfig
            An instance of ApplicationConfig created from the given dictionary.
        """

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
        """Create an ApplicationConfig object from a ConfigParser object.

        Parameters
        ----------
        parser : ConfigParser
            A ConfigParser object containing the configuration.
        name : str
            The name of the application section to parse from the ConfigParser object.
        con_extras : Mapping[str, Any], optional
            Additional configuration parameters to be passed to the ConnectionConfig.from_parser method.
            Defaults to None.

        Returns
        -------
        ApplicationConfig
            An ApplicationConfig object created from the specified section of the ConfigParser object.

        Raises
        ------
        ValueError
            If the application section with the given name is not found in the ConfigParser object.

        Notes
        -----
        The method searches for an application section whose name matches the given name argument,
        and creates an ApplicationConfig object from the configuration parameters within that section.

        If the con_extras argument is provided, it will be passed to the ConnectionConfig.from_parser
        method as an additional configuration parameter.
        """
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
