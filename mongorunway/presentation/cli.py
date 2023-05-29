from __future__ import annotations

import functools
import sys
import typing

import click

from mongorunway.application import applications
from mongorunway.application import use_cases
from mongorunway.presentation import presenters

_P = typing.ParamSpec("_P")
_T = typing.TypeVar("_T")
_CommandT = typing.TypeVar("_CommandT")


def pass_application(command: typing.Callable[_P, _T]) -> typing.Callable[_P, _T]:
    click.option("--config-file", type=click.STRING)(command)

    @click.pass_context
    def wrapper(ctx: click.Context, *args: _P.args, **kwargs: _P.kwargs) -> _T:
        configuration = use_cases.read_configuration(
            ctx.params["config_file"],
            app_name=ctx.params["application_name"],
            verbose_exc=ctx.params.get("verbose_exc", False),
        )

        if configuration is use_cases.UseCaseFailed:
            ctx.fail("Configuration failed.")

        application = applications.MigrationAppImpl(configuration,)
        return typing.cast(
            _T,
            ctx.invoke(command, *args, application=application, **kwargs)
        )

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
    "application_name",
    type=click.STRING,
)
@click.argument(
    "expression",
    default="",
    type=click.STRING,
)
@pass_application
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
    "application_name",
    type=click.STRING,
)
@click.argument(
    "expression",
    default="",
    type=click.STRING,
)
@pass_application
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
@pass_application
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
@pass_application
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
@pass_application
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
    nargs="?",
)
@click.option(
    "-e",
    "--end",
    type=click.STRING,
    default=None,
    nargs="?",
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
@click.argument(
    "application_name",
    type=click.STRING,
)
@pass_application
def auditlog(
    application: applications.MigrationApp,
    start: typing.Optional[typing.Sequence[str]],
    end: typing.Optional[typing.Sequence[str]],
    limit: int,
    ascending: bool,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    presenters.show_auditlog_entries(
        application=application,
        start=start,
        end=end,
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
@pass_application
def version(application: applications.MigrationApp, verbose: bool, **params: typing.Any) -> None:
    presenters.show_version(application=application, verbose=verbose)


if __name__ == "__main__":
    cli()
