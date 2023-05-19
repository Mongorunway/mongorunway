from __future__ import annotations

import typing

import attr

if typing.TYPE_CHECKING:
    from mongorunway import mongo
    from mongorunway.application.ports import filename_strategy as filename_strategy_port
    from mongorunway.application.ports import hook as hook_port

VERSIONING_STARTS_FROM: typing.Final[int] = 1


@attr.define(frozen=True, kw_only=True, repr=True)
class FileSystemConfig:
    scripts_dir: str = attr.field(repr=True)
    config_dir: str = attr.field(repr=False)
    filename_strategy: filename_strategy_port.FilenameStrategy = attr.field(repr=True)
    strict_naming: bool = attr.field(default=True, converter=attr.converters.to_bool, repr=True)


@attr.define(frozen=True, kw_only=True, repr=True, eq=True)
class ApplicationConfig:
    app_client: mongo.Client = attr.field(repr=False)
    app_database: mongo.Database = attr.field(repr=False)
    app_auditlog_collection: mongo.Collection = attr.field(repr=False)
    app_migrations_collection: mongo.Collection = attr.field(repr=False)

    app_name: str = attr.field(validator=attr.validators.min_len(1), repr=True, eq=True)
    app_timezone: str = attr.field(default="UTC", repr=True)
    app_startup_hooks: hook_port.MixedHookList = attr.field(factory=list, repr=False)
    app_auditlog_limit: typing.Optional[int] = attr.field(
        default=None,
        converter=attr.converters.optional(int),
        repr=False,
    )

    use_logging: bool = attr.field(default=True, repr=False, converter=attr.converters.to_bool)
    use_auditlog: bool = attr.field(default=False, repr=False, converter=attr.converters.to_bool)
    use_indexing: bool = attr.field(default=False, converter=attr.converters.to_bool, repr=False)
    use_schema_validation: bool = attr.field(
        default=True,
        converter=attr.converters.to_bool,
        repr=False,
    )

    raise_on_transaction_failure: bool = attr.field(
        default=True, converter=attr.converters.to_bool, repr=False
    )

    def is_auditlog_enabled(self) -> bool:
        return self.app_auditlog_collection is not None and self.use_auditlog

    def is_logged(self) -> bool:
        return self.use_logging

    def has_unique_timezone(self) -> bool:
        return self.app_timezone != "UTC"


@attr.define(frozen=True, kw_only=True, repr=True)
class Config:
    filesystem: FileSystemConfig = attr.field(repr=True)
    application: ApplicationConfig = attr.field(repr=True)
