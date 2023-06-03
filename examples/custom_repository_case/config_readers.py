from __future__ import annotations

__all__: typing.Sequence[str] = ("json_repository_reader",)

import typing

from custom_repository_case import json_repository


def json_repository_reader(
    application_data: typing.Dict[str, typing.Any],
) -> json_repository.JSONRepositoryImpl:
    return json_repository.JSONRepositoryImpl(
        json_filepath=application_data["app_repository"]["json_filepath"],
    )
