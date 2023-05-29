from __future__ import annotations

import typing

from mongorunway import mongo
from mongorunway import util
from mongorunway.infrastructure.persistence import repositories
from mongorunway.infrastructure.persistence import auditlog_journals

if typing.TYPE_CHECKING:
    from mongorunway.application.ports import repository as repository_port
    from mongorunway.application.ports import auditlog_journal as auditlog_journal_port


def default_repository_initializer(
    application_data: typing.Dict[str, typing.Any],
) -> repository_port.MigrationRepository:
    client = mongo.Client(
        **util.build_mapping_values(application_data["app_client"]["init"])
    )
    database = client.get_database(application_data["app_database"])
    collection = database.get_collection(
        application_data["app_repository"]["kwargs"]["collection"]
    )
    return repositories.MigrationRepositoryImpl(collection)


def default_auditlog_journal_initializer(
    application_data: typing.Dict[str, typing.Any],
) -> auditlog_journal_port.AuditlogJournal:
    client = mongo.Client(
        **util.build_mapping_values(application_data["app_client"]["init"])
    )
    database = client.get_database(application_data["app_database"])
    collection = database.get_collection(
        application_data["app_auditlog_journal"]["kwargs"]["collection"]
    )
    return auditlog_journals.AuditlogJournalImpl(collection)
