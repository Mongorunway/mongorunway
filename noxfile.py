from __future__ import annotations

import typing

import nox

MAIN_PKG: typing.Final[str] = "mongorunway"
TESTS_PKG: typing.Final[str] = "tests"
EXAMPLES_PKG: typing.Final[str] = "examples"

PKGS: typing.Final[tuple[str, ...]] = (MAIN_PKG, TESTS_PKG, EXAMPLES_PKG)

BASE_REQUIREMENTS: typing.Final[tuple[str, ...]] = ("-r", "requirements.txt")
DEV_REQUIREMENTS: typing.Final[tuple[str, ...]] = ("-r", "dev-requirements.txt")


@nox.session(python=["3.9", "3.10", "3.11"])
def pytest(session: nox.Session) -> None:
    session.install(*DEV_REQUIREMENTS)
    session.install(*BASE_REQUIREMENTS)

    session.run("pytest")


@nox.session
def reformat_code(session: nox.Session) -> None:
    session.install(*DEV_REQUIREMENTS)
    session.install(*BASE_REQUIREMENTS)

    session.run("black", "--config=pyproject.toml", *PKGS)
    session.run("isort", "--settings-file=pyproject.toml", *PKGS)
