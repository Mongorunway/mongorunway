from __future__ import annotations

import abc
import re
import typing

import yaml

from mongorunway import mongo
from mongorunway import util
from mongorunway.application import config
from mongorunway.application import filesystem
from mongorunway.application.ports import config_reader as config_reader_port
from mongorunway.application.ports import filename_strategy as filename_strategy_port
from mongorunway.domain import migration_event as domain_event
from mongorunway.application.ports import repository as repository_port
from mongorunway.application.ports import auditlog_journal as auditlog_journal_port

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
                handler = util.import_obj(handler_func_path, cast=domain_event.EventHandler)
            except AttributeError as exc:
                raise AttributeError(
                    f"Undefined event handler: {handler_func_path!r}."
                ) from exc

            if priority is not None:
                handler = domain_event.EventHandlerProxy(priority=priority, handler=handler)

            handlers.append(handler)
        else:
            raise ValueError("Invalid handler format.")

    return handlers


def read_events(
    event_dict: typing.Dict[str, typing.Sequence[str]],
) -> typing.Mapping[
    typing.Type[domain_event.MigrationEvent],
    typing.Sequence[domain_event.EventHandlerProxyOr[domain_event.EventHandler]]
]:
    return {
        util.import_obj(event_name, cast=domain_event.MigrationEvent):
        read_event_handlers(handler_name_seq)
        for event_name, handler_name_seq in event_dict.items()
    }


def read_filename_strategy(strategy_path: str) -> filename_strategy_port.FilenameStrategy:
    try:
        strategy_type = util.import_obj(
            strategy_path.strip(),
            cast=filename_strategy_port.FilenameStrategy,
        )
    except AttributeError as exc:
        raise AttributeError(
            f"Undefined filename strategy {strategy_path!r}."
        ) from exc

    return strategy_type()


def read_repository(
    application_data: typing.Dict[str, typing.Any],
) -> repository_port.MigrationRepository:
    try:
        if (repository_value := application_data.get("app_repository")) is None:
            initializer = util.import_obj(
                "mongorunway.infrastructure.initializers.default_repository_initializer",
                cast=typing.Callable[
                    [typing.Dict[str, typing.Any]],
                    repository_port.MigrationRepository,
                ],
            )
            return initializer(application_data)

        if (initializer_value := repository_value.get("initializer")) is not None:
            initializer = util.import_obj(
                initializer_value,
                cast=typing.Callable[
                    [typing.Dict[str, typing.Any]],
                    repository_port.MigrationRepository,
                ],
            )
            return initializer(application_data)

        repository_type = util.import_obj(
            repository_value["type"],
            cast=repository_port.MigrationRepository,
        )

    except AttributeError as exc:
        raise AttributeError(
            f"Undefined initializer or repository received."
        ) from exc

    return repository_type()


def read_auditlog_journal(
    application_data: typing.Dict[str, typing.Any],
) -> typing.Optional[auditlog_journal_port.AuditlogJournal]:
    try:
        if (auditlog_value := application_data.get("app_auditlog_journal")) is None:
            return None

        if (initializer_value := auditlog_value.get("initializer")) is not None:
            initializer = util.import_obj(
                initializer_value,
                cast=typing.Callable[
                    [typing.Dict[str, typing.Any]],
                    auditlog_journal_port.AuditlogJournal,
                ],
            )
            return initializer(application_data)

        auditlog_journal_type = util.import_obj(
            auditlog_value["type"],
            cast=auditlog_journal_port.AuditlogJournal,
        )
    except AttributeError as exc:
        raise AttributeError(
            f"Undefined initializer or repository received."
        ) from exc

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
            logging_dict=configration_data["logging"],
        )

    def _read_filesystem_config(
        self, filesystem_data: typing.Dict[str, typing.Any], config_filepath: str,
    ) -> config.FileSystemConfig:
        return config.FileSystemConfig(
            config_dir=config_filepath,
            scripts_dir=filesystem_data["scripts_dir"],
            filename_strategy=read_filename_strategy(filesystem_data["filename_strategy"]),
            **util.build_optional_kwargs(
                ("strict_naming",),
                filesystem_data,
            ),
        )

    def _read_application_config(
        self, application_data: typing.Dict[str, typing.Any],
    ) -> config.ApplicationConfig:
        return config.ApplicationConfig(
            app_name=self.application_name,
            app_client=(
                client := mongo.Client(
                    **util.build_mapping_values(application_data["app_client"]["init"])
                )
            ),
            app_database=client.get_database(application_data["app_database"]),
            app_repository=read_repository(application_data),
            app_auditlog_journal=read_auditlog_journal(application_data),
            app_subscribed_events=read_events(application_data["app_subscribed_events"]),
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
