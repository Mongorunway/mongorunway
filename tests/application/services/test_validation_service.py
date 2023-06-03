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

import typing

import pytest

from mongorunway.application.services.validation_service import validate_migration_process
from mongorunway.application.services.validation_service import \
    validate_rule_dependencies_recursive
from mongorunway.domain import migration as domain_migration
from mongorunway.domain import migration_business_rule as domain_rule
from mongorunway.domain import migration_exception as domain_exception

if typing.TYPE_CHECKING:
    from mongorunway import mongo


class FakeRuleAlwaysBroken(domain_rule.AbstractMigrationBusinessRule):
    def check_is_broken(self, client: mongo.Client) -> bool:
        return True


class FakeChildRule(domain_rule.AbstractMigrationBusinessRule):
    def __init__(self) -> None:
        super().__init__(depends_on=[FakeRuleAlwaysBroken()])

    def check_is_broken(self, client: mongo.Client) -> bool:
        return False


class FakeChildChildRule(domain_rule.AbstractMigrationBusinessRule):
    def __init__(self) -> None:
        super().__init__(depends_on=[FakeChildRule()])

    def check_is_broken(self, client: mongo.Client) -> bool:
        return False


def test_validate_rule_dependencies_recursive(mongodb: mongo.Database) -> None:
    with pytest.raises(domain_exception.MigrationBusinessRuleBrokenError):
        validate_rule_dependencies_recursive(FakeChildChildRule().depends_on, mongodb.client)


def test_validate_migration_process(mongodb: mongo.Database) -> None:
    process = domain_migration.MigrationProcess(
        commands=[],
        migration_version=1,
        name="abc",
    )
    process.add_rule(FakeChildChildRule())

    with pytest.raises(domain_exception.MigrationBusinessRuleBrokenError):
        validate_migration_process(process, mongodb.client)
