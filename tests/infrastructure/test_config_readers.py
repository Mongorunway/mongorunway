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

from mongorunway.application.ports import auditlog_journal as auditlog_journal_port
from mongorunway.application.ports import repository as repository_port
from mongorunway.domain import migration_event as domain_event
from mongorunway.infrastructure.config_readers import default_auditlog_journal_reader
from mongorunway.infrastructure.config_readers import default_repository_reader
from mongorunway.infrastructure.config_readers import read_auditlog_journal
from mongorunway.infrastructure.config_readers import read_event_handlers
from mongorunway.infrastructure.config_readers import read_events
from mongorunway.infrastructure.config_readers import read_filename_strategy
from mongorunway.infrastructure.config_readers import read_repository
from mongorunway.infrastructure.persistence import auditlog_journals
from mongorunway.infrastructure.persistence import repositories

if typing.TYPE_CHECKING:
    from mongorunway import mongo


class DummyClass:
    pass


class DummyClassAcceptsX:
    def __init__(self, x: int) -> None:
        self.x = x


def fake_event_handler() -> None:
    pass


def fake_repository_reader(data: typing.Dict[str, typing.Any]) -> DummyClassAcceptsX:
    return DummyClassAcceptsX(x=data["app_repository"]["kwargs"]["x"])


def fake_auditlog_journal_reader(data: typing.Dict[str, typing.Any]) -> DummyClassAcceptsX:
    return DummyClassAcceptsX(x=data["app_auditlog_journal"]["kwargs"]["x"])


@pytest.fixture(scope="function")
def default_data(mongodb: mongo.Database) -> typing.Dict[str, typing.Any]:
    return {
        "app_client": {
            "host": "localhost",
            "port": 27017,
        },
        "app_database": mongodb.name,
        "app_auditlog_journal": {
            "collection": "test_auditlog",
        },
        "app_repository": {
            "collection": "test_migrations",
        },
    }


def test_default_auditlog_journal_reader(default_data: typing.Dict[str, typing.Any]) -> None:
    assert isinstance(
        default_auditlog_journal_reader(default_data), auditlog_journals.AuditlogJournalImpl
    )


def test_default_repository_reader(default_data: typing.Dict[str, typing.Any]) -> None:
    assert isinstance(
        default_repository_reader(default_data), repositories.MongoModelRepositoryImpl
    )


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
                    "host": "localhost",
                    "port": 27017,
                },
                "app_database": "TestDatabase",
                "app_repository": {
                    "collection": "test_collection",
                },
            },
            repository_port.MigrationModelRepository,
        ),
        (
            {
                "app_client": {
                    "host": "localhost",
                    "port": 27017,
                },
                "app_database": "TestDatabase",
                "app_repository": {
                    "type": "tests.infrastructure.test_config_readers.DummyClassAcceptsX",
                    "kwargs": {
                        "x": 1,
                    },
                    "reader": "tests.infrastructure.test_config_readers." "fake_repository_reader",
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

    with pytest.raises(KeyError):
        read_repository({})


@pytest.mark.parametrize(
    "application_data, expected_type",
    [
        (
            {
                "app_client": {
                    "host": "localhost",
                    "port": 27017,
                },
                "app_database": "TestDatabase",
                "app_auditlog_journal": {
                    "collection": "test_auditlog",
                },
            },
            auditlog_journal_port.AuditlogJournal,
        ),
        (
            {
                "app_auditlog_journal": {
                    "collection": None,
                },
            },
            type(None),
        ),
        (
            {
                "app_client": {
                    "host": "localhost",
                    "port": 27017,
                },
                "app_database": "TestDatabase",
                "app_auditlog_journal": {
                    "type": "tests.infrastructure.test_config_readers.DummyClassAcceptsX",
                    "kwargs": {
                        "x": 1,
                    },
                    "reader": "tests.infrastructure.test_config_readers."
                    "fake_auditlog_journal_reader",
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


def test_read_filename_strategy() -> None:
    assert isinstance(
        read_filename_strategy("tests.infrastructure.test_config_readers.DummyClass"),
        DummyClass,
    )
