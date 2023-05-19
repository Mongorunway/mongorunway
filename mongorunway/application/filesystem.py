from __future__ import annotations

import os
import typing


def read(filename: str) -> str:
    with open(filename) as file:
        return file.read()


def getcwd() -> str:
    return os.getcwd()


def join(*components: str) -> str:
    return os.path.join(*components)


def find_any(*filenames: str, base_dir: str = os.getcwd()) -> typing.List[str]:
    found_files: typing.List[str] = []

    for dirpath, dirnames, filenames_in_dir in os.walk(base_dir):
        for filename in filenames:
            if filename in filenames_in_dir:
                found_files.append(os.path.join(dirpath, filename))

    return found_files
