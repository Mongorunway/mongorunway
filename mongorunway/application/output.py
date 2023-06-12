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
    "INFO",
    "ERROR",
    "SUCCESS",
    "WARNING",
    "HEADING_MAP",
    "HEADING_LEVEL_ONE",
    "HEADING_LEVEL_TWO",
    "HEADING_LEVEL_THREE",
    "TOOL_HEADING_NAME",
    "AsciiOutput",
    "print",
    "print_heading",
    "print_error",
    "print_success",
    "print_info",
    "print_warning",
    "print_new_line",
    "verbose_print",
)

import enum
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

TOOL_HEADING_NAME: typing.Final[str] = "Mongorunway"


class AsciiOutput(str, enum.Enum):
    INFO = 128712
    DONE = 10003
    WARNING = 9888
    ERROR = 33

    def __str__(self) -> str:
        return chr(self.value)


def print(
    text: str = "",
    bold: bool = False,
    newline: bool = True,
    symbol: str = "",
) -> None:
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
    print(text, bold=bold, symbol=AsciiOutput.DONE)


def print_error(text: str, bold: bool = False) -> None:
    print(text, bold=bold, symbol=AsciiOutput.ERROR)


def print_warning(text: str, bold: bool = False) -> None:
    print(text, bold=bold, symbol=AsciiOutput.WARNING)


def print_info(text: str, bold: bool = False) -> None:
    print(text, bold=bold, symbol=AsciiOutput.INFO)
