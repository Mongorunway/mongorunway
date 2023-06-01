from __future__ import annotations

import types
import typing

import pytest

from mongorunway.application.ports import auditlog_journal as auditlog_journal_port
from mongorunway.application.ports import repository as repository_port
from mongorunway.domain import migration_event as domain_event
from mongorunway.infrastructure.config_readers import read_auditlog_journal
from mongorunway.infrastructure.config_readers import read_event_handlers
from mongorunway.infrastructure.config_readers import read_events
from mongorunway.infrastructure.config_readers import read_filename_strategy
from mongorunway.infrastructure.config_readers import read_repository


class DummyClass:
    pass


class DummyClassAcceptsX:
    def __init__(self, x: int) -> None:
        self.x = x


def fake_event_handler() -> None:
    pass


def fake_repository_initializer(data: typing.Dict[str, typing.Any]) -> DummyClassAcceptsX:
    return DummyClassAcceptsX(x=data["app_repository"]["kwargs"]["x"])


def fake_auditlog_journal_initializer(data: typing.Dict[str, typing.Any]) -> DummyClassAcceptsX:
    return DummyClassAcceptsX(x=data["app_auditlog_journal"]["kwargs"]["x"])


@pytest.mark.parametrize(
    "handler_name, expected_result",
    [
        ("tests.infrastructure.test_config_readers.fake_event_handler", [fake_event_handler]),
        (
            "Prioritized[1, tests.infrastructure.test_config_readers.fake_event_handler]",
            [domain_event.EventHandlerProxy(1, fake_event_handler)],
        ),
    ],
)
def test_read_event_handlers(handler_name: str, expected_result: typing.Any) -> None:
    assert read_event_handlers([handler_name]) == expected_result


@pytest.mark.parametrize(
    "event_name, handler_name_seq, expected_result",
    [
        (
            "tests.infrastructure.test_config_readers.DummyClass",
            ["tests.infrastructure.test_config_readers.fake_event_handler"],
            {DummyClass: [fake_event_handler]},
        ),
        (
            "tests.infrastructure.test_config_readers.DummyClass",
            ["Prioritized[1, tests.infrastructure.test_config_readers.fake_event_handler]"],
            {DummyClass: [domain_event.EventHandlerProxy(1, fake_event_handler)]},
        ),
    ],
)
def test_read_events(
    event_name: str,
    handler_name_seq: typing.Sequence[str],
    expected_result: typing.Any,
) -> None:
    assert read_events({event_name: handler_name_seq}) == expected_result


@pytest.mark.parametrize(
    "application_data, expected_type",
    [
        (
            {
                "app_client": {
                    "init": {
                        "host": "localhost",
                        "port": 27017,
                    },
                },
                "app_database": "TestDatabase",
                "app_auditlog_collection": "test_collection",
            },
            auditlog_journal_port.AuditlogJournal,
        ),
        (
            {
                "app_auditlog_collection": None,
            },
            types.NoneType,
        ),
        (
            {
                "app_client": {
                    "init": {
                        "host": "localhost",
                        "port": 27017,
                    },
                },
                "app_database": "TestDatabase",
                "app_auditlog_journal": {
                    "type": "tests.infrastructure.test_config_readers.DummyClassAcceptsX",
                    "kwargs": {
                        "x": 1,
                    },
                    "initializer": "tests.infrastructure.test_config_readers."
                    "fake_auditlog_journal_initializer",
                },
            },
            DummyClassAcceptsX,
        ),
    ],
)
def test_read_auditlog_journal(
    application_data: typing.Dict[str, typing.Any],
    expected_type: typing.Type[typing.Any],
) -> None:
    assert isinstance(read_auditlog_journal(application_data), expected_type)


@pytest.mark.parametrize(
    "application_data, expected_type",
    [
        (
            {
                "app_client": {
                    "init": {
                        "host": "localhost",
                        "port": 27017,
                    },
                },
                "app_database": "TestDatabase",
                "app_migrations_collection": "test_collection",
            },
            repository_port.MigrationRepository,
        ),
        (
            {
                "app_client": {
                    "init": {
                        "host": "localhost",
                        "port": 27017,
                    },
                },
                "app_database": "TestDatabase",
                "app_repository": {
                    "type": "tests.infrastructure.test_config_readers.DummyClassAcceptsX",
                    "kwargs": {
                        "x": 1,
                    },
                    "initializer": "tests.infrastructure.test_config_readers."
                    "fake_repository_initializer",
                },
            },
            DummyClassAcceptsX,
        ),
    ],
)
def test_read_repository(
    application_data: typing.Dict[str, typing.Any],
    expected_type: typing.Type[typing.Any],
) -> None:
    assert isinstance(read_repository(application_data), expected_type)


def test_read_filename_strategy() -> None:
    assert isinstance(
        read_filename_strategy("tests.infrastructure.test_config_readers.DummyClass"),
        DummyClass,
    )
