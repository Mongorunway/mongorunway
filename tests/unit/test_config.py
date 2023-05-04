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
import dataclasses
import pathlib

import pytest

from mongorunway.kernel.application.config import InvariantsConfig, ApplicationConfig


class TestInvariantsConfig:
    def test_invariants_config_defaults(self) -> None:
        config = InvariantsConfig()
        assert config.versioning_starts_from == 1

    def test_invariants_config_custom(self) -> None:
        config = InvariantsConfig(versioning_starts_from=10)
        assert config.versioning_starts_from == 10

    def test_invariants_config_immutable(self) -> None:
        config = InvariantsConfig(versioning_starts_from=10)
        with pytest.raises(dataclasses.FrozenInstanceError):
            config.versioning_starts_from = 20


class TestApplicationConfig:
    def test_from_dict(self) -> None:
        cfg = ApplicationConfig.from_dict(
            {
                "root": {
                    "scripts_dir": "test_migrations",
                },
                "app_test": {
                    "uri": "localhost",
                    "port": 27017,
                    "database": "test_database",
                    "collection_applied": "applied_migrations",
                    "collection_pending": "pending_migrations",
                }
            },
            name="test",
        )
        assert isinstance(cfg, ApplicationConfig)

    def test_from_ini_file(self, tmp_path: pathlib.Path) -> None:
        with open((cfg_path := str(tmp_path / "cfg.ini")), "w") as f:
            f.write(
                f"[root]\n"
                f"scripts_dir={cfg_path}\n"
                f"[app_test]\n"
                f"uri=localhost\n"
                f"port=27017\n"
                f"database=test_database\n"
                f"collection_applied=applied_migrations\n"
                f"collection_pending=pending_migrations\n"
            )

        cfg = ApplicationConfig.from_ini_file(cfg_path, name="test")
        assert isinstance(cfg, ApplicationConfig)

    def test_from_parser(self) -> None:
        parser = configparser.ConfigParser()

        parser.add_section("root")
        parser.set("root", "scripts_dir", "abc")

        parser.add_section("app_test")
        parser.set("app_test", "uri", "localhost")
        parser.set("app_test", "port", "27017")
        parser.set("app_test", "database", "test_database")
        parser.set("app_test", "collection_applied", "applied_migrations")
        parser.set("app_test", "collection_pending", "pending_migrations")

        cfg = ApplicationConfig.from_parser(parser, name="test")
        assert isinstance(cfg, ApplicationConfig)
