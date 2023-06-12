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
    "FileSystemConfig",
    "Config",
    "ApplicationConfig",
    "VERSIONING_STARTS_FROM",
)

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
    use_filename_strategy: bool = attr.field(
        default=True,
        converter=attr.converters.to_bool,
        repr=True,
    )


@attr.define(frozen=True, kw_only=True, repr=True, eq=True)
class ApplicationConfig:
    app_client: mongo.Client = attr.field(repr=False)
    app_database: mongo.Database = attr.field(repr=False)
    app_repository: repository_port.MigrationModelRepository = attr.field(repr=False)
    app_auditlog_journal: typing.Optional[auditlog_journal_port.AuditlogJournal] = attr.field(
        repr=False,
    )
    app_name: str = attr.field(
        validator=[attr.validators.min_len(1), attr.validators.instance_of(str)],  # type: ignore[arg-type]
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
    app_events: typing.Mapping[
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
