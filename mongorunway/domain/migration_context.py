from __future__ import annotations

import attr

from mongorunway import mongo


@attr.define(frozen=True, repr=True)
class MigrationContext:
    mongorunway_session_id: str = attr.field(repr=True)
    mongodb_session_id: str = attr.field(repr=True)
    client: mongo.Client = attr.field(repr=False)
    database: mongo.Database = attr.field(repr=False)
