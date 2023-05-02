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

import dataclasses
import pathlib
import typing

import pytest
from pytest_bdd import scenario, given, when, then

from mongorunway.kernel.infrastructure.hooks import (
    RecalculateMigrationsChecksum,
    RaiseIfMigrationChecksumMismatch,
)
from mongorunway.kernel.domain.migration_exception import MigrationFileChangedError

if typing.TYPE_CHECKING:
    from mongorunway.kernel.domain.migration import Migration
    from mongorunway.kernel.application.ui import MigrationUI


@dataclasses.dataclass
class RMCContext:  # RecalculateMigrationsChecksum context
    application: MigrationUI
    current_migration_file_state: typing.Optional[Migration]
    current_migration_db_state: typing.Optional[Migration]


@dataclasses.dataclass
class RIMCMContext:  # RaiseIfMigrationChecksumMismatch context
    application: MigrationUI
    current_migration_file_state: typing.Optional[Migration]
    current_migration_db_state: typing.Optional[Migration]


@pytest.fixture(scope="function")
def rmc_ctx(application: MigrationUI) -> RMCContext:
    return RMCContext(
        application=application,
        current_migration_db_state=None,
        current_migration_file_state=None,
    )


@pytest.fixture(scope="function")
def rimcmc_ctx(application: MigrationUI) -> RIMCMContext:
    return RIMCMContext(
        application=application,
        current_migration_db_state=None,
        current_migration_file_state=None,
    )


@scenario("test_hooks.feature", "Recalculate migration checksum when a file is modified")
def test_recalculate_migrations_checksum() -> None:
    """This test allows to verify the work of hooks for the migration application using a
    structured approach based on scenarios and test steps. This allows to better organize
    complex testing logic and ensure more comprehensive coverage of the application functionality.
    Each test step describes a specific stage of the testing process, making it more readable and
    understandable for all project participants.
    """
    pass


@given("we have a configured migration application")
def reconfigure_migration_application(rmc_ctx: RMCContext, tmp_path: pathlib.Path) -> None:
    # Reloading temp migrations dir
    rmc_ctx.application.config.migration_scripts_dir = str(tmp_path)


@when("we create a migration file and obtain a complete migration object for further testing")
def create_complete_migration_object(rmc_ctx: RMCContext, migration: Migration) -> None:
    rmc_ctx.application.create_migration_file_template(migration.name, migration.version)
    rmc_ctx.current_migration_file_state = rmc_ctx.application.get_migration_from_filename(
        migration.name,
    )


@when("we add the obtained migration to the database, simulating a real use case")
def append_migration_to_database(rmc_ctx: RMCContext) -> None:
    assert rmc_ctx.current_migration_file_state is not None

    rmc_ctx.application.pending.append_migration(rmc_ctx.current_migration_file_state)
    rmc_ctx.current_migration_db_state = rmc_ctx.application.pending.acquire_migration(
        rmc_ctx.current_migration_file_state.version,
    )


@then("we check if their checksums are equal")
def verify_checksum_equality(rmc_ctx: RMCContext) -> None:
    assert (
        rmc_ctx.current_migration_file_state.checksum == rmc_ctx.current_migration_db_state.checksum
    )


@when("we open the migration file and modify it, thereby changing the checksum of the migration")
def check_modification_changes_checksum(rmc_ctx: RMCContext, migration: Migration) -> None:
    with open(rmc_ctx.application.config.migration_scripts_dir + fr"\{migration.name}.py", "a") as f:
        f.write("# File is changed")


@then(
    "we obtain the current state of the modified migration file and the unchanged migration from the database"
    "\nand assert that their checksums are not equal, as the file has been modified"
)
def check_modified_migration_checksum_not_equal_to_original(
    rmc_ctx: RMCContext, migration: Migration,
) -> None:
    current_migration_file_state = rmc_ctx.application.get_migration_from_filename(migration.name)
    current_migration_db_state = rmc_ctx.application.pending.acquire_migration(migration.version)

    assert current_migration_db_state.checksum != current_migration_file_state.checksum


@when(
    "we create a hook that allows resolving this conflict by recalculating all checksums and apply "
    "it to the application"
)
def resolve_checksum_conflict_by_recalculation(rmc_ctx: RMCContext) -> None:
    hook = RecalculateMigrationsChecksum()
    hook.apply(rmc_ctx.application)


@then(
    "we obtain the current state of the migration from the file and the current state of the migration\n"
    "in the database and assert that they are equal, as the hook that recalculates their checksums has\n"
    "been applied."
)
def verify_migration_consistency_after_hook(rmc_ctx: RMCContext, migration: Migration) -> None:
    current_migration_file_state = rmc_ctx.application.get_migration_from_filename(migration.name)
    current_migration_db_state = rmc_ctx.application.pending.acquire_migration(migration.version)

    assert current_migration_db_state.checksum == current_migration_file_state.checksum


@scenario("test_hooks.feature", "Raise if migration file checksum mismatch")
def test_raise_if_migration_checksum_mismatch() -> None:
    """This test allows to verify the work of hooks for the migration application using a
    structured approach based on scenarios and test steps. This allows to better organize
    complex testing logic and ensure more comprehensive coverage of the application functionality.
    Each test step describes a specific stage of the testing process, making it more readable and
    understandable for all project participants.
    """
    pass


@given("we have a configured migration application")
def reconfigure_migration_application(rimcmc_ctx: RIMCMContext, tmp_path: pathlib.Path) -> None:
    # Reloading temp migrations dir
    rimcmc_ctx.application.config.migration_scripts_dir = str(tmp_path)


@when("we create a migration file and obtain a complete migration object for further testing")
def create_complete_migration_object(rimcmc_ctx: RIMCMContext, migration: Migration) -> None:
    rimcmc_ctx.application.create_migration_file_template(migration.name, migration.version)
    rimcmc_ctx.current_migration_file_state = rimcmc_ctx.application.get_migration_from_filename(
        migration.name,
    )


@when("we add the obtained migration to the database, simulating a real use case")
def append_migration_to_database(rimcmc_ctx: RIMCMContext) -> None:
    assert rimcmc_ctx.current_migration_file_state is not None

    rimcmc_ctx.application.pending.append_migration(rimcmc_ctx.current_migration_file_state)
    rimcmc_ctx.current_migration_db_state = rimcmc_ctx.application.pending.acquire_migration(
        rimcmc_ctx.current_migration_file_state.version,
    )


@then("we check if their checksums are equal")
def verify_checksum_equality(rimcmc_ctx: RIMCMContext) -> None:
    assert (
        rimcmc_ctx.current_migration_file_state.checksum == rimcmc_ctx.current_migration_db_state.checksum
    )


@then("we apply the hook and it doesn't throw an exception because the migration file hasn't changed")
def hook_applied_successfully_migration_file_unchanged(rimcmc_ctx: RIMCMContext) -> None:
    hook = RaiseIfMigrationChecksumMismatch()
    hook.apply(rimcmc_ctx.application)


@when("we open the migration file and modify it, thereby changing the checksum of the migration")
def check_modification_changes_checksum(rimcmc_ctx: RIMCMContext, migration: Migration) -> None:
    with open(rimcmc_ctx.application.config.migration_scripts_dir + fr"\{migration.name}.py", "a") as f:
        f.write("# File is changed")


@then(
    "we apply the hook after changing the migration file and get a MigrationFileChangedError exception\n"
    "because the migration file has been changed"
)
def hook_application_migration_file_changed_error_exception_raised(rimcmc_ctx: RIMCMContext) -> None:
    hook = RaiseIfMigrationChecksumMismatch()

    with pytest.raises(MigrationFileChangedError):
        hook.apply(rimcmc_ctx.application)
