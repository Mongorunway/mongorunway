from __future__ import annotations

__all__ = ("create_app", "raise_if_migration_version_mismatch", "migration", "migration_with_rule")

import collections.abc
import functools
import typing

from mongorunway.application import applications
from mongorunway.application import use_cases
from mongorunway.domain import migration as domain_migration
from mongorunway.infrastructure.persistence import auditlog_journals
from mongorunway.infrastructure.persistence import repositories

if typing.TYPE_CHECKING:
    from mongorunway.application.applications import MigrationApp
    from mongorunway.application.ports import auditlog_journal as auditlog_journal_port
    from mongorunway.domain import migration_business_rule as domain_rule

_P = typing.ParamSpec("_P")
_T = typing.TypeVar("_T")


@typing.overload
def create_app(
    name: str,
    config_filepath: str,
    *,
    raise_on_none: typing.Literal[True] = True,
) -> MigrationApp:
    ...


@typing.overload
def create_app(
    name: str,
    config_filepath: str,
    *,
    raise_on_none: typing.Literal[False] = False,
) -> typing.Optional[MigrationApp]:
    ...


def create_app(
    name: str,
    config_filepath: str,
    *,
    raise_on_none: bool = False,
    verbose_exc: bool = False,
) -> typing.Union[MigrationApp, typing.Optional[MigrationApp]]:
    configuration = use_cases.read_configuration(
        config_filepath=config_filepath,
        app_name=name,
        verbose_exc=verbose_exc,
    )
    if configuration is not use_cases.UseCaseFailed:
        auditlog_journal: typing.Optional[auditlog_journal_port.AuditlogJournal] = None
        if configuration.application.is_logged():
            auditlog_journal = auditlog_journals.AuditlogJournalImpl(
                auditlog_collection=configuration.application.app_auditlog_collection,
                max_records=configuration.application.app_auditlog_limit,
            )

        return applications.MigrationAppImpl(
            configuration=configuration,
            repository=repositories.MigrationRepositoryImpl(
                migrations_collection=configuration.application.app_migrations_collection,
            ),
            auditlog_journal=auditlog_journal,
            startup_hooks=configuration.application.app_startup_hooks,
        )

    if raise_on_none:
        raise ValueError(f"Creation of {name!r} application is failed.")

    return None


def raise_if_migration_version_mismatch(
    app: applications.MigrationApp,
    expected_version: typing.Union[int, typing.Callable[[], int]],
) -> None:
    if callable(expected_version):
        expected_version = expected_version()

    if (current_version := (app.session.get_current_version() or 0)) != expected_version:
        raise ValueError(
            f"Migration version mismatch. "
            f"Actual: {current_version!r}, but {expected_version!r} expected."
        )


def migration(process_func: typing.Callable[_P, _T], /) -> domain_migration.MigrationProcess:
    # @functools.wraps(process_func)
    # def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> domain_migration.MigrationProcess:
    commands = process_func()
    if isinstance(commands, domain_migration.MigrationProcess):
        return commands

    if not isinstance(commands, collections.abc.MutableSequence):
        raise ValueError(
            f"Migration process func {process_func!r} must return sequence of commands."
        )

    version = getattr(process_func, "__globals__", {}).get("version", None)
    if version is None:
        raise ValueError(
            f"Migration module at {process_func.__code__.co_filename!r} "
            f"should have 'version' variable."
        )

    return domain_migration.MigrationProcess(
        commands,
        migration_version=version,
        name=getattr(process_func, "__name__", ""),
    )


def migration_with_rule(rule: domain_rule.MigrationBusinessRule, /):
    return lambda p: p.add_rule(rule)
