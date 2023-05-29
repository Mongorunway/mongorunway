from __future__ import annotations

__all__: typing.Sequence[str] = (
    "validate_migration_process",
    "validate_rule_dependencies_recursive",
)

import logging
import typing

from mongorunway import mongo
from mongorunway.domain import migration_business_rule as domain_rule
from mongorunway.domain import migration_exception as domain_exception
from mongorunway.domain import migration as domain_migration

_LOGGER: typing.Final[logging.Logger] = logging.getLogger("mongorunway.validation_service")


def validate_rule_dependencies_recursive(
    depends_on: typing.Sequence[domain_rule.MigrationBusinessRule],
    client: mongo.Client,
) -> None:
    for rule in depends_on:
        if rule.check_is_broken(client):
            _LOGGER.error("%s rule failed, raising...", rule.name)
            raise domain_exception.MigrationBusinessRuleBrokenError(rule)

        _LOGGER.info("%s rule successfully passed.", rule.name)

        if rule.is_independent():
            continue

        validate_rule_dependencies_recursive(
            client=client,
            depends_on=rule.depends_on,
        )


def validate_migration_process(
    migration_process: domain_migration.MigrationProcess,
    client: mongo.Client,
) -> None:
    if migration_process.has_rules():
        _LOGGER.info(
            "Starting validation of migration process with version %s...",
            migration_process.migration_version,
        )

        for rule in migration_process.rules:
            if not rule.is_independent():
                validate_rule_dependencies_recursive(
                    client=client,
                    depends_on=rule.depends_on,
                )

            if rule.check_is_broken(client):
                _LOGGER.error("%s rule failed, raising...", rule.name)
                raise domain_exception.MigrationBusinessRuleBrokenError(rule)

            _LOGGER.info("%s rule successfully passed.", rule.name)
