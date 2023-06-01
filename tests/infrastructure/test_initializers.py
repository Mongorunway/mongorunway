from __future__ import annotations

import typing

import pytest

from mongorunway.infrastructure.initializers import default_auditlog_journal_initializer
from mongorunway.infrastructure.initializers import default_repository_initializer
from mongorunway.infrastructure.persistence.auditlog_journals import AuditlogJournalImpl
from mongorunway.infrastructure.persistence.repositories import MigrationRepositoryImpl

if typing.TYPE_CHECKING:
    from mongorunway import mongo


@pytest.fixture(scope="function")
def default_data(mongodb: mongo.Database) -> typing.Dict[str, typing.Any]:
    return {
        "app_client": {
            "init": {
                "host": "localhost",
                "port": 27017,
            },
        },
        "app_database": mongodb.name,
        "app_migrations_collection": "test_migrations",
        "app_auditlog_collection": "test_auditlog",
    }


def test_default_auditlog_journal_initializer(default_data: typing.Dict[str, typing.Any]) -> None:
    assert isinstance(default_auditlog_journal_initializer(default_data), AuditlogJournalImpl)


def test_default_repository_initializer(default_data: typing.Dict[str, typing.Any]) -> None:
    assert isinstance(default_repository_initializer(default_data), MigrationRepositoryImpl)
