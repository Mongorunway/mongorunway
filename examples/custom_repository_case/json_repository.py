from __future__ import annotations

__all__: typing.Sequence[str] = ("JSONRepositoryImpl",)

import json
import operator
import threading
import typing

from mongorunway.application.ports import repository as repository_port
from mongorunway.domain import migration as domain_migration


class JSONRepositoryImpl(repository_port.MigrationModelRepository):
    def __init__(self, json_filepath: str) -> None:
        self._fp = json_filepath
        self._lock = threading.RLock()  # Use reentrant lock to allow nested acquire/release

    def __len__(self) -> int:
        with self._lock:
            return len(self._get_migrations())

    def __contains__(self, item: typing.Any, /) -> bool:
        with self._lock:
            return self.has_migration(item)

    def has_migration(self, item: typing.Any, /) -> bool:
        with self._lock:
            if hasattr(item, "version"):
                item = item.version
            return self._get_migrations().get(item) is not None

    def has_migration_with_version(self, migration_version: int, /) -> bool:
        with self._lock:
            return self._get_migrations().get(migration_version) is not None

    def has_migrations(self) -> bool:
        with self._lock:
            return bool(self._get_migrations())

    def acquire_migration_model_by_version(
        self,
        migration_version: int,
    ) -> typing.Optional[domain_migration.MigrationReadModel]:
        with self._lock:
            try:
                model_dict = self._get_migrations()[migration_version]
            except KeyError:
                return None

        return domain_migration.MigrationReadModel.from_dict(model_dict)

    def acquire_migration_model_by_flag(
        self, is_applied: bool
    ) -> typing.Optional[domain_migration.MigrationReadModel]:
        with self._lock:
            migrations = [
                v for v in self._get_migrations().values() if v["is_applied"] is is_applied
            ]
            if not migrations:
                return None

            migrations.sort(key=operator.itemgetter("version"))
            if is_applied:
                # LIFO
                migrations.reverse()

            model = domain_migration.MigrationReadModel.from_dict(migrations[0])

        return model

    def acquire_all_migration_models(
        self,
        *,
        ascending_id: bool = True,
    ) -> typing.Iterator[domain_migration.MigrationReadModel]:
        with self._lock:
            migrations = list(self._get_migrations().values())

            migrations.sort(key=operator.itemgetter("version"))
            if not ascending_id:
                migrations.reverse()

        while migrations:
            try:
                schema = migrations.pop(0)
            except StopIteration:
                break

            yield domain_migration.MigrationReadModel.from_dict(schema)

    def acquire_migration_models_by_flag(
        self,
        *,
        is_applied: bool,
    ) -> typing.Iterator[domain_migration.MigrationReadModel]:
        with self._lock:
            migrations = list(self._get_migrations().values())

            if is_applied:
                migrations.reverse()

        while migrations:
            try:
                schema = migrations.pop(0)
            except StopIteration:
                break

            yield domain_migration.MigrationReadModel.from_dict(schema)

    def append_migration(self, migration: domain_migration.Migration, /) -> int:
        with self._lock:
            with open(self._fp, "r+") as file:
                data = json.load(file)
                data.update(
                    {migration.version: migration.to_dict(unique=False)},
                )

                file.seek(0)
                json.dump(data, file)

        return migration.version

    def remove_migration(self, migration_version: int, /) -> int:
        with self._lock:
            migrations = self._get_migrations()
            with open(self._fp, "w") as f:
                migrations.pop(migration_version)
                json.dump(migrations, f)

        return migration_version

    def set_applied_flag(self, migration: domain_migration.Migration, is_applied: bool) -> int:
        with self._lock:
            migrations = self._get_migrations()
            with open(self._fp, "w") as f:
                migrations[migration.version]["is_applied"] = is_applied
                json.dump(migrations, f)

        return migration.version

    def _get_migrations(self) -> typing.Dict[int, typing.Dict[str, typing.Any]]:
        with self._lock:
            with open(self._fp, "r", encoding="utf-8") as file:
                data = file.read()
                if not json.loads(data):
                    return {}

                migrations = {int(k): v for k, v in json.loads(data).items()}

        return migrations
