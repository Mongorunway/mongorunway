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

import configparser
import logging
from unittest import mock

import pytest
import pymongo
import pymongo.database

from mongorunway.kernel.infrastructure.filename_strategies import NumericalFilenameStrategy
from mongorunway.kernel.application.config import (
    RuntimeConfig,
    AuditlogConfig,
    StartupConfig,
    ConnectionConfig,
    LoggingConfig,
)


class TestRuntimeConfig:
    @pytest.fixture
    def parser(self) -> configparser.ConfigParser:
        parser = configparser.ConfigParser()
        parser.add_section("runtime")
        parser.set("runtime", "strict_naming", "false")

        # The non-existent default strategy will be replaced with NumericalFilenameStrategy.
        parser.set("runtime", "filename_strategy", "my.custom.filename_strategy.CustomFilenameStrategy")

        parser.set("runtime", "raise_if_nothing_happens", "false")
        return parser

    def test_from_parser_defaults(self, parser: configparser.ConfigParser) -> None:
        config = RuntimeConfig.from_parser(parser)
        assert not config.strict_naming
        assert not config.raise_if_nothing_happens
        assert isinstance(config.filename_strategy, NumericalFilenameStrategy)

    def test_from_parser_missing_values(self, parser: configparser.ConfigParser) -> None:
        parser.remove_section("runtime")
        config = RuntimeConfig.from_parser(parser)
        assert config.strict_naming
        assert config.raise_if_nothing_happens
        assert isinstance(config.filename_strategy, NumericalFilenameStrategy)


class TestConnectionConfig:
    @pytest.fixture
    def config_parser(self) -> configparser.ConfigParser:
        parser = configparser.ConfigParser()

        parser.add_section("app_test")
        parser.set("app_test", "uri", "mongodb://localhost")
        parser.set("app_test", "port", "27017")
        parser.set("app_test", "database", "test_db")
        parser.set("app_test", "collection_applied", "applied_migrations")
        parser.set("app_test", "collection_pending", "pending_migrations")
        parser.set("app_test", "username", "test_user")
        parser.set("app_test", "password", "test_password")

        return parser

    @pytest.fixture
    def mock_mongo_client(self) -> mock.MagicMock:
        return mock.MagicMock(spec=pymongo.MongoClient)

    @pytest.fixture
    def mock_mongo_database(self) -> mock.MagicMock:
        return mock.MagicMock(spec=pymongo.database.Database)

    @pytest.fixture
    def mock_applied_migration_collection(self) -> mock.MagicMock:
        return mock.MagicMock(spec=pymongo.collection.Collection)

    @pytest.fixture
    def mock_pending_migration_collection(self) -> mock.MagicMock:
        return mock.MagicMock(spec=pymongo.collection.Collection)

    def test_connection_config_from_parser_calls_mongo_client_constructor(
        self,
        config_parser: configparser.ConfigParser,
        mock_mongo_client: mock.MagicMock,
    ) -> None:
        with mock.patch(
            "pymongo.MongoClient", return_value=mock_mongo_client
        ) as mock_mongo_client_constructor:
            ConnectionConfig.from_parser(config_parser, application_name="test", con_extras={})

            mock_mongo_client_constructor.assert_called_once_with(
                "mongodb://localhost",
                27017,
                **{"username": "test_user", "password": "test_password"},
            )

    def test_connection_config_from_parser_calls_mongo_database_constructor(
        self,
        config_parser: configparser.ConfigParser,
        mock_mongo_client: mock.MagicMock,
        mock_mongo_database: mock.MagicMock,
    ) -> None:
        with mock.patch("pymongo.MongoClient", return_value=mock_mongo_client):
            with mock.patch.object(
                mock_mongo_client, "get_database", return_value=mock_mongo_database
            ) as mock_database_constructor:
                ConnectionConfig.from_parser(config_parser, application_name="test", con_extras={})
                mock_database_constructor.assert_called_once_with("test_db")

    def test_connection_config_from_parser_calls_migration_collection_constructor(
        self,
        config_parser: configparser.ConfigParser,
        mock_mongo_client: mock.MagicMock,
        mock_mongo_database: mock.MagicMock,
        mock_applied_migration_collection: mock.MagicMock,
        mock_pending_migration_collection: mock.MagicMock,
    ) -> None:
        # Set up side_effect for get_collection to return appropriate collections
        mock_mongo_database.get_collection.side_effect = [
            mock_applied_migration_collection,
            mock_pending_migration_collection,
        ]

        with mock.patch("pymongo.MongoClient", return_value=mock_mongo_client):
            with mock.patch.object(mock_mongo_client, "get_database", return_value=mock_mongo_database):
                # Call from_parser
                ConnectionConfig.from_parser(config_parser, application_name="test", con_extras={})

                # Check that get_collection was called twice with the correct arguments
                mock_mongo_database.get_collection.assert_has_calls(
                    [mock.call("applied_migrations"), mock.call("pending_migrations")]
                )


class TestLoggingConfig:
    @pytest.fixture()
    def config_parser(self) -> configparser.ConfigParser:
        parser = configparser.ConfigParser()
        parser.read_dict(
            {
                "log": {
                    "level": "DEBUG",
                },
            },
        )
        return parser

    def test_from_parser(self, config_parser: configparser.ConfigParser) -> None:
        logging_config = LoggingConfig.from_parser(config_parser)
        assert logging_config.level == logging.DEBUG

    def test_from_parser_with_default(self, config_parser: configparser.ConfigParser) -> None:
        # Remove the log section from the parser to test the fallback to the default value
        config_parser.remove_section("log")
        logging_config = LoggingConfig.from_parser(config_parser)
        assert logging_config.level == logging.INFO

    def test_from_parser_with_invalid_value(self, config_parser: configparser.ConfigParser) -> None:
        # Set an invalid value for the log level to test the fallback to the default value
        config_parser.set("log", "level", "invalid_level")
        logging_config = LoggingConfig.from_parser(config_parser)
        assert logging_config.level == logging.INFO


class TestAuditlogConfig:
    @pytest.fixture
    def config_parser(self) -> configparser.ConfigParser:
        parser = configparser.ConfigParser()

        parser.add_section("app_test")
        parser.set("app_test", "uri", "mongodb://localhost")
        parser.set("app_test", "port", "27017")
        parser.set("app_test", "database", "test_db")
        parser.set("app_test", "collection_applied", "applied_migrations")
        parser.set("app_test", "collection_pending", "pending_migrations")

        parser.add_section("app_test.auditlog")
        parser.set("app_test.auditlog", "collection_auditlog", "test_auditlog_collection")

        return parser

    @pytest.fixture
    def connection_config(self, config_parser: configparser.ConfigParser) -> ConnectionConfig:
        return ConnectionConfig.from_parser(config_parser, application_name="test", con_extras={})

    @pytest.fixture
    def mock_collection(self) -> mock.MagicMock:
        return mock.MagicMock(spec=pymongo.collection.Collection)

    def test_from_parser_returns_instance_with_none_collection_when_section_not_found(
        self, config_parser: configparser.ConfigParser, connection_config: ConnectionConfig,
    ) -> None:
        config_parser.remove_section("app_test.auditlog")

        config = AuditlogConfig.from_parser(
            config_parser, application_name="test", connection_config=connection_config
        )

        assert config.auditlog_collection is None

    def test_from_parser_returns_instance_with_target_collection(
        self,
        config_parser: configparser.ConfigParser,
        connection_config: ConnectionConfig,
        mock_collection: mock.MagicMock,
    ) -> None:
        with mock.patch.object(
            connection_config.mongo_database, "get_collection", return_value=mock_collection
        ):
            config = AuditlogConfig.from_parser(
                config_parser, application_name="test", connection_config=connection_config
            )

            assert config.auditlog_collection is mock_collection
            connection_config.mongo_database.get_collection.assert_called_once_with(
                "test_auditlog_collection"
            )


class TestStartupConfig:
    @pytest.fixture()
    def parser(self) -> configparser.ConfigParser:
        parser = configparser.ConfigParser()
        parser.read_dict(
            {
                "app_test.on_startup": {
                    "raise_if_migrations_checksum_mismatch": "true",
                    "sync_scripts_with_queues": "false",
                    "recalculate_migrations_checksum": "true",
                }
            }
        )
        return parser

    def test_startup_config_from_parser(self, parser: configparser.ConfigParser) -> None:
        startup_config = StartupConfig.from_parser(parser, application_name="test")
        assert startup_config.raise_if_migrations_checksum_mismatch
        assert not startup_config.sync_scripts_with_queues
        assert startup_config.recalculate_migrations_checksum

    def test_startup_config_from_parser_with_defaults(self, parser: configparser.ConfigParser) -> None:
        parser.remove_section("app_test.on_startup")
        startup_config = StartupConfig.from_parser(parser, application_name="test")
        assert startup_config.raise_if_migrations_checksum_mismatch
        assert startup_config.sync_scripts_with_queues
        assert not startup_config.recalculate_migrations_checksum
