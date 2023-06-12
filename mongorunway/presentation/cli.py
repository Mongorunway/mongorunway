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
    "pass_application",
    "auditlog",
    "create_template",
    "cli",
    "status",
    "walk",
    "downgrade",
    "upgrade",
    "refresh",
    "version",
    "init",
    "safe_remove",
    "safe_remove_all",
    "check_files",
    "refresh_checksums",
)

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

        application = applications.MigrationAppImpl(configuration)
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
    "--verbose-exc",
    is_flag=True,
    help="Enable verbose output for exceptions during the upgrade process.",
)
@click.argument(
    "application_name",
    type=click.STRING,
    metavar="APPLICATION_NAME",
    required=True,
)
@click.argument(
    "expression",
    type=click.STRING,
    default="+",
    metavar="EXPRESSION",
    required=False,
)
@pass_application
def upgrade(
    application: applications.MigrationApp,
    expression: str,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    """Upgrade the specified application.

    This command allows you to upgrade the specified application using the
    given expression or additional arguments. Optionally, you can enable
    verbose output or verbose output for exceptions during the upgrade process.
    """

    exit_code = use_cases.upgrade(
        application=application,
        expression=expression,
        verbose_exc=verbose_exc,
    )
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--verbose-exc",
    is_flag=True,
    help="Enable verbose output for exceptions during the downgrade process.",
)
@click.argument(
    "application_name",
    type=click.STRING,
    metavar="APPLICATION_NAME",
    required=True,
)
@click.argument(
    "expression",
    type=click.STRING,
    default="-",
    metavar="EXPRESSION",
    required=False,
)
@pass_application
def downgrade(
    application: applications.MigrationApp,
    expression: str,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    """Downgrade the specified application.

    This command allows you to downgrade the specified application using the
    given expression or additional arguments. Optionally, you can enable verbose
    output or verbose output for exceptions during the downgrade process.
    """

    exit_code = use_cases.downgrade(
        application=application,
        expression=expression,
        verbose_exc=verbose_exc,
    )
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--verbose-exc",
    is_flag=True,
    help="Enable verbose output for exceptions during the walk process.",
)
@click.argument(
    "application_name",
    type=click.STRING,
    metavar="APPLICATION_NAME",
    required=True,
)
@click.argument(
    "expression",
    type=click.STRING,
    metavar="EXPRESSION",
    required=True,
)
@pass_application
def walk(
    application: applications.MigrationApp,
    expression: str,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    """
    Walk through the specified application.

    This command allows you to perform a walk operation on the specified
    application using the given expression or additional arguments. The
    walk operation enables you to traverse the application's structure or
    perform specific actions.

    Optionally, you can enable verbose output or verbose output for exceptions
    during the walk process.
    """

    exit_code = use_cases.walk(
        application=application,
        expression=expression,
        verbose_exc=verbose_exc,
    )
    sys.exit(exit_code)


@cli.command()
@click.option(
    "-n", "--name", type=click.STRING, help="Specify the name of the migration template."
)
@click.option(
    "-v",
    "--version",
    type=click.INT,
    default=None,
    required=False,
    help="Specify the version number of the migration template.",
)
@click.option(
    "--verbose-exc",
    is_flag=True,
    help="Enable verbose output for exceptions during the template creation process.",
)
@click.argument(
    "application_name",
    type=click.STRING,
    metavar="APPLICATION_NAME",
    required=True,
)
@pass_application
def create_template(
    application: applications.MigrationApp,
    name: str,
    verbose_exc: bool,
    version: typing.Optional[int] = None,
    **params: typing.Any,
) -> None:
    """Create a migration template for the specified application.

    This command allows you to create a migration template for the specified
    application. The template can be customized with a name and an optional
    version number.

    Optionally, you can enable verbose output for exceptions during the
    template creation process.
    """

    exit_code = use_cases.create_migration_file(
        application=application,
        migration_filename=name,
        migration_version=version,
        verbose_exc=verbose_exc,
    )
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--verbose-exc",
    is_flag=True,
    help="Enable verbose exception mode.",
)
@click.argument(
    "application_name",
    type=click.STRING,
    metavar="APPLICATION_NAME",
    required=True,
)
@pass_application
def refresh(
    application: applications.MigrationApp,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    """Refreshes the specified application.

    This command refreshes the specified application by performing certain actions.
    It accepts an APPLICATION_NAME as a required argument and provides an option
    to enable verbose exception mode using the --verbose-exc flag.
    """
    exit_code = use_cases.refresh(
        application=application,
        verbose_exc=verbose_exc,
    )
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--verbose-exc",
    is_flag=True,
    help="Enable verbose output for exceptions during the status command.",
)
@click.option(
    "-d",
    "--depth",
    type=click.INT,
    default=-1,
    required=False,
    help="Specify the depth of the migration history to display.",
)
@click.argument(
    "application_name",
    type=click.STRING,
    metavar="APPLICATION_NAME",
    required=True,
)
@pass_application
def status(
    application: applications.MigrationApp,
    depth: int,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    """Display the migration status for the specified application.

    This command allows you to view the migration status of the specified
    application. It shows the history of applied migrations up to the
    specified depth.

    Optionally, you can enable verbose output for the status command and
    verbose output for exceptions that may occur during the status check.
    """

    presenters.show_status(
        application=application,
        pushed_depth=depth,
        verbose_exc=verbose_exc,
    )


@cli.command()
@click.option(
    "-s",
    "--start",
    type=click.STRING,
    default=None,
    nargs="?",
    help="Specify the start timestamp or date for filtering audit log entries.",
)
@click.option(
    "-e",
    "--end",
    type=click.STRING,
    default=None,
    nargs="?",
    help="Specify the end timestamp or date for filtering audit log entries.",
)
@click.option(
    "-l",
    "--limit",
    type=click.INT,
    default=10,
    help="Specify the maximum number of audit log entries to display.",
)
@click.option(
    "-a",
    "--ascending",
    is_flag=True,
    help="Sort the audit log entries in ascending order by date.",
)
@click.option(
    "--verbose-exc",
    is_flag=True,
    help="Enable verbose output for exceptions during the audit log command.",
)
@click.argument(
    "application_name",
    type=click.STRING,
    metavar="APPLICATION_NAME",
    required=True,
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
    """Display the audit log entries for the specified application.

    This command allows you to view the audit log entries for the
    specified application. You can filter the entries by specifying a
    start and/or end timestamp or date. The maximum number of entries
    displayed can be limited, and you can choose to sort the entries
    in ascending order by date.

    Optionally, you can enable verbose output for exceptions that may
    occur during the audit log command.
    """

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
    "--verbose-exc",
    is_flag=True,
    help="Enable verbose output for exceptions during the version command.",
)
@click.argument(
    "application_name",
    type=click.STRING,
    metavar="APPLICATION_NAME",
    required=True,
)
@pass_application
def version(application: applications.MigrationApp, **params: typing.Any) -> None:
    """Display the version information for the specified application.

    This command allows you to view the version information of the
    specified application. It shows details such as the application's
    name, version number, and other relevant details.

    Optionally, you can enable verbose output for the version command
    to get more detailed information.
    """

    presenters.show_version(application=application)


@cli.command()
@click.option(
    "--verbose-exc",
    is_flag=True,
    help="Enable verbose output for exceptions during the init command.",
)
@click.option(
    "--scripts-dir",
    is_flag=True,
    help="Initialize the scripts directory for the specified application.",
)
@click.option(
    "--collection", is_flag=True, help="Initialize the collection for the specified application."
)
@click.option(
    "--indexes",
    is_flag=True,
    help="Initialize the indexes for the specified application's collection.",
)
@click.option(
    "--schema-validation",
    is_flag=True,
    help="Enable schema validation for the specified application's collection.",
)
@click.argument(
    "application_name",
    type=click.STRING,
    metavar="APPLICATION_NAME",
    required=True,
)
@pass_application
def init(
    application: applications.MigrationApp,
    scripts_dir: bool,
    collection: bool,
    indexes: bool,
    verbose_exc: bool,
    schema_validation: bool,
    **params: typing.Any,
) -> None:
    """Initialize the specified application for migration.

    This command allows you to initialize the specified application
    for migration. You can choose to initialize the scripts directory,
    collection, indexes, and enable schema validation for the
    application's collection.

    Initializing the scripts directory will create the necessary
    directory structure for storing migration scripts.

    Initializing the collection will create the migration collection in
    the database.

    Initializing the indexes will create the required indexes for the
    migration collection.

    Enabling schema validation will enforce the defined schema on the
    migration collection.

    Note: Use caution when running the init command as it may modify
    the application's database.

    Optionally, you can enable verbose output for exceptions that may
    occur during the init command.
    """

    exit_code = use_cases.init(
        application=application,
        verbose_exc=verbose_exc,
        init_scripts_dir=scripts_dir,
        init_collection=collection,
        init_collection_indexes=indexes,
        init_collection_schema_validation=schema_validation,
    )
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--verbose-exc",
    is_flag=True,
    help="Enable verbose exception output.",
)
@click.argument(
    "application_name",
    type=click.STRING,
    metavar="APPLICATION_NAME",
    required=True,
)
@click.argument(
    "migration_version",
    type=click.INT,
    metavar="MIGRATION_VERSION",
    required=True,
)
@pass_application
def safe_remove(
    application: applications.MigrationApp,
    migration_version: int,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    """Safely removes a migration from the specified application.

    This command allows you to safely remove a migration from the
    specified application. It ensures that the removal process is
    handled securely and provides an option to enable verbose
    exception output for detailed error messages.
    """

    exit_code = use_cases.safe_remove_migration(
        application=application,
        migration_version=migration_version,
        verbose_exc=verbose_exc,
    )
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--verbose-exc",
    is_flag=True,
    help="Enable verbose exception output.",
)
@click.argument(
    "application_name",
    type=click.STRING,
    metavar="APPLICATION_NAME",
    required=True,
)
@pass_application
def safe_remove_all(
    application: applications.MigrationApp,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    """Safely removes all migrations from the specified application.

    This command allows you to safely remove all migrations from the
    specified application. It ensures that the removal process is
    handled securely and provides an option to enable verbose exception
    output for detailed error messages.
    """

    exit_code = use_cases.safe_remove_all_migrations(
        application=application,
        verbose_exc=verbose_exc,
    )
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--verbose-exc",
    is_flag=True,
    help="Enable verbose exception output.",
)
@click.option(
    "--raise-exc",
    is_flag=True,
    help="Throws an exception if a mismatch is found.",
)
@click.argument(
    "application_name",
    type=click.STRING,
    metavar="APPLICATION_NAME",
    required=True,
)
@pass_application
def check_files(
    application: applications.MigrationApp,
    raise_exc: bool,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    """Check the integrity of files in the specified application.

    This command verifies the integrity of files in the specified
    application. It compares the checksums of the files stored in
    the repository with the checksums of the corresponding files
    in the file system. If any differences are found, an appropriate
    message is displayed.
    """

    exit_code = use_cases.check_files(
        application=application,
        raise_exc=raise_exc,
        verbose_exc=verbose_exc,
    )
    sys.exit(exit_code)


@cli.command()
@click.option(
    "--verbose-exc",
    is_flag=True,
    help="Enable verbose exception output.",
)
@click.argument(
    "application_name",
    type=click.STRING,
    metavar="APPLICATION_NAME",
    required=True,
)
@pass_application
def refresh_checksums(
    application: applications.MigrationApp,
    verbose_exc: bool,
    **params: typing.Any,
) -> None:
    """Refresh the checksums of files in the specified application.

    This command updates the checksums of files in the specified
    application. It recalculates the checksums of all files in the
    repository and updates them accordingly. This can be useful when
    the files in the application have been modified or when the
    checksums need to be synchronized with the repository.
    """

    exit_code = use_cases.refresh_checksums(
        application=application,
        verbose_exc=verbose_exc,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    cli()
