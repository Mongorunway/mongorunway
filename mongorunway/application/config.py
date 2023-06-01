from __future__ import annotations

import typing

import attr

if typing.TYPE_CHECKING:
    from mongorunway import mongo
    from mongorunway.application.ports import auditlog_journal as auditlog_journal_port
    from mongorunway.application.ports import filename_strategy as filename_strategy_port
    from mongorunway.application.ports import repository as repository_port
    from mongorunway.domain import migration_event as domain_event

VERSIONING_STARTS_FROM: typing.Final[int] = 1


@attr.define(frozen=True, kw_only=True, repr=True)
class FileSystemConfig:
    scripts_dir: str = attr.field(repr=True, validator=attr.validators.instance_of(str))
    config_dir: str = attr.field(repr=False, validator=attr.validators.instance_of(str))
    filename_strategy: filename_strategy_port.FilenameStrategy = attr.field(repr=True)
    strict_naming: bool = attr.field(default=True, converter=attr.converters.to_bool, repr=True)


@attr.define(frozen=True, kw_only=True, repr=True, eq=True)
class ApplicationConfig:
    app_client: mongo.Client = attr.field(repr=False)
    app_database: mongo.Database = attr.field(repr=False)
    app_repository: repository_port.MigrationRepository = attr.field(repr=False)
    app_auditlog_journal: typing.Optional[auditlog_journal_port.AuditlogJournal] = attr.field(
        repr=False,
    )
    app_name: str = attr.field(
        validator=[attr.validators.min_len(1), attr.validators.instance_of(str)],
        repr=True,
        eq=True,
    )
    app_timezone: str = attr.field(
        validator=attr.validators.instance_of(str),
        default="UTC",
        repr=True,
    )
    app_date_format: str = attr.field(
        default="%Y-%m-%d %H:%M:%S",
        validator=attr.validators.instance_of(str),
    )
    app_subscribed_events: typing.Mapping[
        typing.Type[domain_event.MigrationEvent],
        typing.Sequence[domain_event.EventHandlerProxyOr[domain_event.EventHandler]],
    ] = attr.field(factory=dict, repr=False)
    app_auditlog_limit: typing.Optional[int] = attr.field(
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(int)),
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

    @property
    def is_auditlog_enabled(self) -> bool:
        return self.app_auditlog_journal is not None and self.use_auditlog

    @property
    def is_logged(self) -> bool:
        return self.use_logging

    @property
    def has_unique_timezone(self) -> bool:
        return self.app_timezone != "UTC"


@attr.define(frozen=True, kw_only=True, repr=True)
class Config:
    filesystem: FileSystemConfig = attr.field(repr=True)
    application: ApplicationConfig = attr.field(repr=True)
    logging_dict: typing.Dict[str, typing.Any]
