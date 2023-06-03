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
    "validate_migration_process",
    "validate_rule_dependencies_recursive",
)

import logging
import typing

from mongorunway import mongo
from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_business_rule as domain_rule
from mongorunway.domain import migration_exception as domain_exception

if typing.TYPE_CHECKING:
    from mongorunway.domain import migration_context as domain_context

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("mongorunway.validation_service")


def validate_rule_dependencies_recursive(
    depends_on: typing.Sequence[domain_rule.MigrationBusinessRule],
    ctx: domain_context.MigrationContext,
) -> None:
    for rule in depends_on:
        if rule.check_is_broken(ctx):
            _LOGGER.error("%s rule failed, raising...", rule.name)
            raise domain_exception.MigrationBusinessRuleBrokenError(rule)

        _LOGGER.info("%s rule successfully passed.", rule.name)

        if rule.is_independent():
            continue

        validate_rule_dependencies_recursive(
            ctx=ctx,
            depends_on=rule.depends_on,
        )


def validate_migration_process(
    migration_process: domain_migration.MigrationProcess,
    ctx: domain_context.MigrationContext,
) -> None:
    if migration_process.has_rules():
        _LOGGER.info(
            "Starting validation of migration process with version %s...",
            migration_process.migration_version,
        )

        for rule in migration_process.rules:
            if not rule.is_independent():
                validate_rule_dependencies_recursive(
                    ctx=ctx,
                    depends_on=rule.depends_on,
                )

            if rule.check_is_broken(ctx):
                _LOGGER.error("%s rule failed, raising...", rule.name)
                raise domain_exception.MigrationBusinessRuleBrokenError(rule)

            _LOGGER.info("%s rule successfully passed.", rule.name)
