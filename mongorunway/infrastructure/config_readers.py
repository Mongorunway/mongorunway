from __future__ import annotations

import abc
import configparser
import typing

from mongorunway import mongo
from mongorunway import util
from mongorunway.application import config
from mongorunway.application import filesystem
from mongorunway.application.ports import config_reader as config_reader_port
from mongorunway.application.ports import filename_strategy as filename_strategy_port

if typing.TYPE_CHECKING:
    from mongorunway.application.ports import hook as hook_port

# Not totally correct from a DDD perspective, but the solution could be justified
# by optimizing theuser API, so that hook handling is "hidden from view". Ideally,
# the infrastructure layer should provide an API for the application layer to use,
# while remaining decoupled. However, for pragmatic reasons, importing from the
# infrastructure layer into the application layer could be used temporarily as an
# "optimization hack", if properly argued and documented to avoid degrading code
# maintainability.
from mongorunway.infrastructure import filename_strategies
from mongorunway.infrastructure import hooks


def read_hooks(hook_name_list: typing.List[str]) -> hook_port.MixedHookList:
    app_hooks: hook_port.MixedHookList = []
    prioritized = "Prioritized"

    for hook_name in hook_name_list:
        hook_name = hook_name.strip()
        priority = -1

        if hook_name.startswith(prioritized):
            if hook_name[len(prioritized) :][0] != "[":
                raise ValueError("Square bracket not open.")
            if hook_name[-1] != "]":
                raise ValueError("Square bracket not closed.")

            args = hook_name[len(prioritized) + 1 : -1].split(",")
            if not args[0].strip().isdigit():
                raise ValueError(
                    "The first parameter of a prioritized hook must be a numeric priority."
                )

            hook_name = args[1].strip()
            priority = abs(int(args[0]))  # Priority cannot be negative

        try:
            hook = getattr(hooks, hook_name)()
        except AttributeError as exc:
            raise AttributeError(f"Undefined hook: {hook_name!r}.") from exc

        if priority != -1:
            hook = hooks.PrioritizedMigrationHookImpl(priority, hook)

        app_hooks.append(hook)

    return app_hooks


def read_filename_strategy(strategy_name: str) -> filename_strategy_port.FilenameStrategy:
    try:
        strategy = getattr(filename_strategies, strategy_name.strip())()
    except AttributeError as exc:
        raise AttributeError(f"Undefined filename strategy: {strategy_name!r}.") from exc

    return typing.cast(filename_strategy_port.FilenameStrategy, strategy)


class BaseConfigReader(config_reader_port.ConfigReader):
    potential_config_filenames: typing.List[str]

    def __init__(self, application_name: str) -> None:
        self.application_name = application_name

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
            config = self._read_config(config_filepath)
            if config:
                return config

        return None

    @abc.abstractmethod
    def _read_config(self, config_filepath: str) -> typing.Optional[config.Config]:
        ...


class IniFileConfigReader(BaseConfigReader):
    potential_config_filenames = ["mongorunway.ini"]

    def _read_config(self, config_filepath: str) -> typing.Optional[config.Config]:
        configuration = configparser.ConfigParser(
            # This converter allows you to parse hooks via 'getlist()' in the format:
            #     hook = Hook1
            #            Hook2
            #            ...
            # Note: This format does not support commas.
            converters=dict(list=lambda x: [i.strip() for i in x.splitlines()]),
        )
        configuration.read(config_filepath)

        return config.Config(
            filesystem=self._read_filesystem_config(configuration, config_filepath),
            application=self._read_application_config(configuration),
        )

    def _read_filesystem_config(
        self,
        configuration: configparser.ConfigParser,
        config_filepath: str,
    ) -> config.FileSystemConfig:
        config_mapping = configuration["filesystem"]

        return config.FileSystemConfig(
            config_dir=config_filepath,
            filename_strategy=read_filename_strategy(
                config_mapping.get("filename_strategy", "NumericalFilenameStrategy"),
            ),
            scripts_dir=config_mapping["scripts_dir"],
            **util.build_optional_kwargs(
                ("strict_naming",),
                config_mapping,
            ),
        )

    def _read_application_config(
        self,
        configuration: configparser.ConfigParser,
    ) -> config.ApplicationConfig:
        section = "application_" + self.application_name
        if not configuration.has_section(conn_section := (section + "." + "client_kwargs")):
            raise KeyError(f"Missing {conn_section!r} required section in configuration file.")

        client = mongo.Client(**util.build_mapping_values(dict(configuration[conn_section])))

        return config.ApplicationConfig(
            app_name=self.application_name,
            app_client=client,
            app_database=(
                database := client.get_database(configuration.get(section, "app_database"))
            ),
            app_auditlog_collection=database.get_collection(
                configuration.get(
                    section,
                    "app_auditlog_collection",
                    fallback=None,  # type: ignore[arg-type]
                )
            ),
            app_migrations_collection=database.get_collection(
                configuration.get(section, "app_migrations_collection")
            ),
            app_startup_hooks=read_hooks(
                configuration.getlist(section, "app_startup_hooks")  # type: ignore[attr-defined]
            ),
            **util.build_optional_kwargs(
                (
                    "app_timezone",
                    "app_auditlog_limit",
                    "use_logging",
                    "use_auditlog",
                    "use_indexing",
                    "use_schema_validation",
                    "raise_on_transaction_failure",
                ),
                configuration[section],
            ),
        )
