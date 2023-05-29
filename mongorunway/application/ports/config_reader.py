from __future__ import annotations

__all__: typing.Sequence[str] = ("ConfigReader",)

import abc
import typing

if typing.TYPE_CHECKING:
    from mongorunway.application import config


class ConfigReader(abc.ABC):
    __slots__ = ()

    @classmethod
    @abc.abstractmethod
    def from_application_name(cls, application_name: str, /) -> ConfigReader:
        ...

    @abc.abstractmethod
    def read_config(
        self,
        config_filename: typing.Optional[str] = None,
    ) -> typing.Optional[config.Config]:
        ...
