from __future__ import annotations

import abc
import typing

if typing.TYPE_CHECKING:
    from mongorunway.application import config


class ConfigReader(abc.ABC):
    __slots__ = ()

    @abc.abstractmethod
    def read_config(
        self,
        config_filename: typing.Optional[str] = None,
    ) -> typing.Optional[config.Config]:
        ...
