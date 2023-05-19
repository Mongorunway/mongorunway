from __future__ import annotations

import typing

# In a public tool, dependency on CLI is an essential part, so in this case,
# we can ignore the Dependency Inversion Principle and implement output with
# a specific implementation using click.
import click

INFO = "info"
ERROR = "error"
SUCCESS = "success"
WARNING = "warning"

HEADING_LEVEL_ONE = 1
HEADING_LEVEL_TWO = 2
HEADING_LEVEL_THREE = 3

HEADING_MAP = {
    HEADING_LEVEL_ONE: ("=", True),
    HEADING_LEVEL_TWO: ("-", True),
    HEADING_LEVEL_THREE: ("-", False),
}

SYMBOLS = {INFO: "*", ERROR: "!", SUCCESS: "✓", WARNING: "⚠"}

TOOL_HEADING_NAME: typing.Final[str] = "Mongorunway"


def print(text: str = "", bold: bool = False, newline: bool = True, symbol: str = "") -> None:
    if symbol:
        text = symbol + " " + text

    click.secho(text, bold=bold, nl=newline)


def verbose_print(
    verbose: bool,
    text: str = "",
    bold: bool = False,
    newline: bool = True,
    symbol: str = "",
) -> None:
    if verbose:
        print(
            text=text,
            bold=bold,
            symbol=symbol,
            newline=newline,
        )


def print_new_line(count: int = 1) -> None:
    for i in range(count):
        click.secho()


def print_heading(level: int, text: str, indent: bool = True) -> None:
    line_char, show_line_above = HEADING_MAP[level]
    heading_line = line_char * len(text)

    if show_line_above:
        print(heading_line, bold=True)

    print(text, bold=True)
    print(heading_line, bold=True)

    if indent:
        print_new_line()


def print_success(text: str, bold: bool = False) -> None:
    print(text, bold=bold, symbol=SYMBOLS[SUCCESS])


def print_error(text: str, bold: bool = False) -> None:
    print(text, bold=bold, symbol=SYMBOLS[ERROR])


def print_warning(text: str, bold: bool = False) -> None:
    print(text, bold=bold, symbol=SYMBOLS[WARNING])


def print_info(text: str, bold: bool = False) -> None:
    print(text, bold=bold, symbol=SYMBOLS[INFO])
