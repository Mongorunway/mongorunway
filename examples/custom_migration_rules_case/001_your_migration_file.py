from __future__ import annotations

import typing

from custom_migration_rules_case.custom_rules import RequiredCollRule

import mongorunway

version = 1


@mongorunway.migration
def upgrade() -> typing.Sequence[mongorunway.MigrationCommand]:
    return []


@mongorunway.migration_with_rule(RequiredCollRule())
@mongorunway.migration
def downgrade() -> typing.Sequence[mongorunway.MigrationCommand]:
    return []
