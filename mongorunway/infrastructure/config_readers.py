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
    "default_repository_reader",
    "default_auditlog_journal_reader",
    "read_repository",
    "read_events",
    "read_event_handlers",
    "read_auditlog_journal",
    "read_filename_strategy",
    "BaseConfigReader",
    "YamlConfigReader",
)

import abc
import re
import typing

import yaml  # type: ignore[import]

from mongorunway import mongo
from mongorunway import util
from mongorunway.application import config
from mongorunway.application import filesystem
from mongorunway.application.ports import auditlog_journal as auditlog_journal_port
from mongorunway.application.ports import config_reader as config_reader_port
from mongorunway.application.ports import filename_strategy as filename_strategy_port
from mongorunway.application.ports import repository as repository_port
from mongorunway.domain import migration_event as domain_event
from mongorunway.infrastructure.persistence import auditlog_journals
from mongorunway.infrastructure.persistence import repositories

event_handler_pattern: typing.Pattern[str] = re.compile(
    r"""
    ^                  # Start of the string
    Prioritized\[      # Match the literal string "Prioritized["
        (\d+),         # Group 1: Match one or more digits (priority)
        \s*            # Match zero or more whitespace characters
        (.+)           # Group 2: Match one or more characters (handler function path)
    \]$                # Match the closing square bracket and end of the string
    |                  # OR
    ^                  # Start of the string
    ([^,\[\]]+)        # Group 3: Match any characters except comma, square brackets
    $                  # End of the string
    """,
    flags=re.VERBOSE,
)

logging_config: typing.Dict[str, typing.Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simpleFormatter": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "consoleHandler": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simpleFormatter",
        }
    },
    "loggers": {"root": {"level": "INFO", "handlers": ["consoleHandler"], "propagate": 0}},
}


def default_repository_reader(
    application_data: typing.Dict[str, typing.Any],
) -> repository_port.MigrationModelRepository:
    client = mongo.Client(**util.build_mapping_values(application_data["app_client"]))
    database = client.get_database(application_data["app_database"])
    collection = database.get_collection(application_data["app_repository"]["collection"])
    return repositories.MongoModelRepositoryImpl(collection)


def default_auditlog_journal_reader(
    application_data: typing.Dict[str, typing.Any],
) -> typing.Optional[auditlog_journal_port.AuditlogJournal]:
    if (collection := application_data["app_auditlog_journal"].get("collection")) is None:
        return None

    client = mongo.Client(**util.build_mapping_values(application_data["app_client"]))
    database = client.get_database(application_data["app_database"])
    collection = database.get_collection(collection)
    return auditlog_journals.AuditlogJournalImpl(collection)


@typing.no_type_check
def read_event_handlers(
    handler_name_seq: typing.Sequence[str],
) -> typing.List[domain_event.EventHandlerProxyOr[domain_event.EventHandler]]:
    handlers: typing.List[domain_event.EventHandlerProxyOr[domain_event.EventHandler]] = []

    for handler_name in handler_name_seq:
        match = re.match(event_handler_pattern, handler_name)
        if match:
            if match.group(1):  # If there is a group 1, then there is a structure "Priority".
                priority = int(match.group(1))
                handler_func_path = match.group(2)
            else:
                priority = None
                handler_func_path = match.group(3)

            try:
                print(654654, handler_func_path)
                handler = util.import_obj(handler_func_path, cast=domain_event.EventHandler)
            except AttributeError as exc:
                raise AttributeError(f"Undefined event handler: {handler_func_path!r}.") from exc

            if priority is not None:
                handler = domain_event.EventHandlerProxy(priority=priority, handler=handler)

            handlers.append(handler)
        else:
            raise ValueError("Invalid handler format.")

    return handlers


@typing.no_type_check
def read_events(
    event_dict: typing.Dict[str, typing.Sequence[str]],
) -> typing.Mapping[
    typing.Type[domain_event.MigrationEvent],
    typing.Sequence[domain_event.EventHandlerProxyOr[domain_event.EventHandler]],
]:
    try:
        mapping = {
            util.import_obj(event_name, cast=domain_event.MigrationEvent): read_event_handlers(
                handler_name_seq
            )
            for event_name, handler_name_seq in event_dict.items()
        }
    except AttributeError as exc:
        raise AttributeError(f"Undefined event or event handler.") from exc

    return mapping


@typing.no_type_check
def read_filename_strategy(strategy_path: str) -> filename_strategy_port.FilenameStrategy:
    try:
        strategy_type = util.import_obj(
            strategy_path.strip(),
            cast=filename_strategy_port.FilenameStrategy,
        )
    except AttributeError as exc:
        raise AttributeError(f"Undefined filename strategy {strategy_path!r}.") from exc

    return strategy_type()


@typing.no_type_check
def read_repository(
    application_data: typing.Dict[str, typing.Any],
) -> repository_port.MigrationModelRepository:
    try:
        if (repository_data := application_data.get("app_repository")) is None:
            raise KeyError("Missing 'app_repository' section.")

        if (reader_value := repository_data.get("reader")) is not None:
            reader = util.import_obj(
                reader_value,
                cast=typing.Callable[
                    [typing.Dict[str, typing.Any]],
                    repository_port.MigrationModelRepository,
                ],
            )
            return reader(application_data)

        if (repo_type := application_data.get("type")) is None:
            reader = util.import_obj(
                "mongorunway.infrastructure.config_readers.default_repository_reader",
                cast=typing.Callable[
                    [typing.Dict[str, typing.Any]],
                    repository_port.MigrationModelRepository,
                ],
            )
            return reader(application_data)

        repository_type = util.import_obj(
            repo_type,
            cast=repository_port.MigrationModelRepository,
        )

    except AttributeError as exc:
        raise AttributeError(f"Undefined reader or repository received.") from exc

    return repository_type()


@typing.no_type_check
def read_auditlog_journal(
    application_data: typing.Dict[str, typing.Any],
) -> typing.Optional[auditlog_journal_port.AuditlogJournal]:
    try:
        if (auditlog_value := application_data.get("app_auditlog_journal")) is None:
            return None

        if (reader_value := auditlog_value.get("reader")) is not None:
            reader = util.import_obj(
                reader_value,
                cast=typing.Callable[
                    [typing.Dict[str, typing.Any]],
                    auditlog_journal_port.AuditlogJournal,
                ],
            )
            return reader(application_data)

        if (audit_type := application_data.get("type")) is None:
            reader = util.import_obj(
                "mongorunway.infrastructure.config_readers.default_auditlog_journal_reader",
                cast=typing.Callable[
                    [typing.Dict[str, typing.Any]],
                    auditlog_journal_port.AuditlogJournal,
                ],
            )
            return reader(application_data)

        auditlog_journal_type = util.import_obj(
            audit_type,
            cast=auditlog_journal_port.AuditlogJournal,
        )
    except AttributeError as exc:
        raise AttributeError(f"Undefined reader or repository received.") from exc

    return auditlog_journal_type()


class BaseConfigReader(config_reader_port.ConfigReader):
    potential_config_filenames: typing.List[str]

    def __init__(self, application_name: str) -> None:
        self.application_name = application_name

    @classmethod
    def from_application_name(cls, application_name: str, /) -> config_reader_port.ConfigReader:
        return cls(application_name=application_name)

    def read_config(
        self,
        config_filepath: typing.Optional[str] = None,
    ) -> typing.Optional[config.Config]:
        if config_filepath:
            config_filepaths = filesystem.find_any(config_filepath)
            if not config_filepaths:
                raise FileNotFoundError(f"Could not find {config_filepath!r} configuration file.")
        else:
            config_filepaths = filesystem.find_any(*self.potential_config_filenames)
            if not config_filepaths:
                return None

        # Search until at least one config is found
        for config_filepath in config_filepaths:
            configuration = self._read_config(config_filepath)
            if configuration:
                return configuration

        return None

    @abc.abstractmethod
    def _read_config(self, config_filepath: str) -> typing.Optional[config.Config]:
        ...


class YamlConfigReader(BaseConfigReader):
    potential_config_filenames = ["mongorunway.yaml"]

    def _read_config(self, config_filepath: str) -> typing.Optional[config.Config]:
        with open(config_filepath, "r") as config_file:
            configration_data = yaml.safe_load(config_file)["mongorunway"]

        return config.Config(
            filesystem=self._read_filesystem_config(
                configration_data["filesystem"],
                config_filepath,
            ),
            application=self._read_application_config(
                configration_data["applications"][self.application_name],
            ),
            logging_dict=configration_data.get("logging", logging_config),
        )

    def _read_filesystem_config(
        self,
        filesystem_data: typing.Dict[str, typing.Any],
        config_filepath: str,
    ) -> config.FileSystemConfig:
        return config.FileSystemConfig(
            config_dir=config_filepath,
            scripts_dir=filesystem_data["scripts_dir"],
            filename_strategy=read_filename_strategy(
                filesystem_data.get(
                    "filename_strategy",
                    "mongorunway.infrastructure.filename_strategies.NumericalFilenameStrategy",
                ),
            ),
            **util.build_optional_kwargs(
                ("strict_naming",),
                filesystem_data,
            ),
        )

    def _read_application_config(
        self,
        application_data: typing.Dict[str, typing.Any],
    ) -> config.ApplicationConfig:
        return config.ApplicationConfig(
            app_name=self.application_name,
            app_client=(
                client := mongo.Client(**util.build_mapping_values(application_data["app_client"]))
            ),
            app_database=client.get_database(application_data["app_database"]),
            app_repository=read_repository(application_data),
            app_auditlog_journal=read_auditlog_journal(application_data),
            app_subscribed_events=read_events(application_data.get("app_subscribed_events", {})),
            **util.build_optional_kwargs(
                (
                    "app_timezone",
                    "app_date_format",
                    "app_auditlog_limit",
                    "use_logging",
                    "use_auditlog",
                    "use_indexing",
                    "use_schema_validation",
                    "raise_on_transaction_failure",
                ),
                application_data,
            ),
        )
