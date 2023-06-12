# Use API case

Mongorunway provides a comprehensive user API, and in this example, we will explore the 
usage of its basic functionality. For more detailed information about Mongorunway's features, 
you can refer to the `API Reference` section.

## IN:

```py
import pprint

import mongorunway
from mongorunway.application.services import migration_service
from mongorunway.application import use_cases

# Creating an application with the `raise_on_none` and `verbose_exc`
# parameters for more detailed debugging.
app = mongorunway.create_app("test", raise_on_none=True, verbose_exc=True)

# The application encapsulates all event manager methods.
@app.listen()
def on_app_close(event: mongorunway.ClosingEvent) -> None:
    print(f"{event.application.name!r} app successfully closed.")

# Create a migration service that interacts with the file system
# and will be useful for creating a migration template file.
service = migration_service.MigrationService(app.session)

# By default, the status indicator to which no migration has been
# applied is set to builtins.None. The version count starts from one.
assert app.session.get_current_version() is None

# Create a template migration file with the name `my_awesome_migration`.
service.create_migration_file_template("my_awesome_migration")

# The file is not synchronized with the database during creation.
# To synchronize the file system with the database, we can use the
# corresponding use case.
assert len(app.session.get_all_migration_models()) == 0

# Synchronize the file system with the database.
use_cases.refresh(app, verbose_exc=True)

# Verify that the synchronization was successful and the migration
# was added to the database.
assert len(app.session.get_all_migration_models()) == 1

# Next, we can use the lower-level API (migration application methods) or
# the higher-level API (use cases). Let's explore the first option.
app.upgrade_once()

# Since we have configured the audit log in the configuration, let's check 
# its functionality.
assert app.session.uses_auditlog
for entry in app.session.history():
    pprint.pprint(entry)
```

## OUT:
```py
MigrationAuditlogEntry(session_id=Binary(b'@\x96\x1c\x93\xaa\x83O_\xb9\xceO\xb7y\xc0R\x9f', 4),
                    transaction_name='UpgradeTransaction',
                    migration_read_model=MigrationReadModel(name='001_my_awesome_migration',
                                                            version=1,
                                                            checksum='76b6a991ca38100583cc75b020da77fc',
                                                            description='',
                                                            is_applied=False),
                    date_fmt='%Y-%m-%d %H:%M:%S',
                    date=datetime.datetime(2023, 6, 12, 14, 48, 50, 199000),
                    exc_name=None,
                    exc_message=None)

```
```py
'test' app successfully closed.
```
