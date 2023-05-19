from __future__ import annotations

import datetime
import functools
import sys
import typing

import click

from mongorunway.application import applications
from mongorunway.application import use_cases
from mongorunway.infrastructure.persistence import auditlog_journals
from mongorunway.infrastructure.persistence import repositories
from mongorunway.presentation import presenters

if typing.TYPE_CHECKING:
    from mongorunway.application.ports import auditlog_journal as auditlog_journal_port

_P = typing.ParamSpec("_P")
_T = typing.TypeVar("_T")
_CommandT = typing.TypeVar("_CommandT")


def application_aware(command: typing.Callable[_P, _T]) -> typing.Callable[_P, _T]:
    click.argument("application_name", type=click.STRING)(command)
    click.option("--config-file", type=click.STRING, envvar="MONGORUNWAY_CONFIG_FILE")(command)

    @click.pass_context
    def wrapper(ctx: click.Context, *args: _P.args, **kwargs: _P.kwargs) -> _T:
        configuration = use_cases.read_configuration(
            ctx.params["config_file"],
            app_name=ctx.params["application_name"],
            verbose_exc=ctx.params.get("verbose_exc", False),
        )

        journal: typing.Optional[auditlog_journal_port.AuditlogJournal] = None
        if configuration.application.is_logged():
            # For type checkers only
            assert configuration.application.app_auditlog_collection is not None

            journal = auditlog_journals.AuditlogJournalImpl(
                auditlog_collection=configuration.application.app_auditlog_collection,
                max_records=configuration.application.app_auditlog_limit,
            )

        application = applications.MigrationAppImpl(
            configuration=configuration,
            repository=repositories.MigrationRepositoryImpl(
                migrations_collection=configuration.application.app_migrations_collection,
            ),
            auditlog_journal=journal,
            startup_hooks=configuration.application.app_startup_hooks,
        )
        return typing.cast(_T, ctx.invoke(command, *args, application=application, **kwargs))

    return typing.cast(
        typing.Callable[_P, _T],
        functools.update_wrapper(wrapper, command),
    )


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.option(
    "--verbose",
    is_flag=True,
)
@click.option(
    "--verbose-exc",
    is_flag=True,
)
@click.argument(
    "expression",
    default="",
    type=click.STRING,
)
@application_aware
def upgrade(
    application: applications.MigrationApp,
    expression: str,
    verbose: bool,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    exit_code = use_cases.upgrade(
        application=application,
        expression=expression,
        verbose=verbose,
        verbose_exc=verbose_exc,
    )
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--verbose",
    is_flag=True,
)
@click.option(
    "--verbose-exc",
    is_flag=True,
)
@click.argument(
    "expression",
    default="",
    type=click.STRING,
)
@application_aware
def downgrade(
    application: applications.MigrationApp,
    expression: str,
    verbose: bool,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    exit_code = use_cases.downgrade(
        application=application,
        expression=expression,
        verbose=verbose,
        verbose_exc=verbose_exc,
    )
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--verbose",
    is_flag=True,
)
@click.option(
    "--verbose-exc",
    is_flag=True,
)
@click.argument(
    "expression",
    default="",
    type=click.STRING,
)
@application_aware
def walk(
    application: applications.MigrationApp,
    expression: str,
    verbose: bool,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    exit_code = use_cases.walk(
        application=application,
        expression=expression,
        verbose=verbose,
        verbose_exc=verbose_exc,
    )
    sys.exit(exit_code)


@cli.command()
@click.option(
    "-n",
    "--name",
    type=click.STRING,
)
@click.option(
    "-v",
    "--version",
    type=click.INT,
    default=None,
    required=False,
)
@click.option(
    "--verbose-exc",
    is_flag=True,
)
@application_aware
def create_template(
    application: applications.MigrationApp,
    name: str,
    verbose_exc: bool,
    version: typing.Optional[int] = None,
    **params: typing.Any,
) -> None:
    exit_code = use_cases.create_migration_file(
        application=application,
        migration_filename=name,
        migration_version=version,
        verbose_exc=verbose_exc,
    )
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--verbose",
    is_flag=True,
)
@click.option(
    "--verbose-exc",
    is_flag=True,
)
@click.option(
    "-d",
    "--depth",
    type=click.INT,
    default=-1,
    required=False,
)
@application_aware
def status(
    application: applications.MigrationApp,
    depth: int,
    verbose: bool,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    presenters.show_status(
        application=application,
        pushed_depth=depth,
        verbose=verbose,
        verbose_exc=verbose_exc,
    )


@cli.command()
@click.option(
    "-s",
    "--start",
    type=click.STRING,
    default=None,
    nargs=2,
)
@click.option(
    "-e",
    "--end",
    type=click.STRING,
    default=None,
    nargs=2,
)
@click.option(
    "-l",
    "--limit",
    type=click.INT,
    default=10,
)
@click.option(
    "-a",
    "--ascending",
    is_flag=True,
)
@click.option(
    "--verbose-exc",
    is_flag=True,
)
@application_aware
def auditlog(
    application: applications.MigrationApp,
    start: typing.Optional[typing.Tuple[str, str]],
    end: typing.Optional[typing.Tuple[str, str]],
    limit: int,
    ascending: bool,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    # TODO: Implement a more flexible mechanism for handling time.
    def _convert(
        date_parts: typing.Optional[typing.Tuple[str, str]],
    ) -> typing.Optional[datetime.datetime]:
        if date_parts is None:
            return None

        return datetime.datetime.strptime(
            " ".join(date_parts),
            "%Y-%m-%d %H:%M:%S",
        )

    presenters.show_auditlog_entries(
        application=application,
        start=_convert(start),
        end=_convert(end),
        limit=limit,
        verbose_exc=verbose_exc,
        ascending_date=ascending,
    )


@cli.command()
@click.option(
    "--verbose",
    is_flag=True,
)
@click.option(
    "--verbose-exc",
    is_flag=True,
)
@application_aware
def version(application: applications.MigrationApp, verbose: bool, **params: typing.Any) -> None:
    presenters.show_version(application=application, verbose=verbose)


if __name__ == "__main__":
    cli()
