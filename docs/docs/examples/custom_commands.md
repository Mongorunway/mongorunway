# Custom commands case

Mongorunway is not limited to a set of standard commands, and you can create your 
own commands as needed. An example of such implementation is provided below.

## Step-by-Step Configuration of the Migration Environment

In this section, we will walk through the step-by-step configuration of the migration 
environment for the proper functioning of the tool.

### Project structure

```html
migrations/
  <!-- This file is optional and is -->
  <!-- used only for example purposes. -->
  001_create_abc_collection.py
  
  <!-- You can see the implementation of -->
  <!-- this file below this code block    -->
  002_attach_abc_collection.py

  <!-- In this transit file, it will be convenient for us -->
  <!-- to store our custom component implementations.     -->
  __init__.py
  mongorunway.yaml
```

Next, we will present and discuss the implementations of the components in this 
project structure.

#### `002_attach_abc_collection.py`
```py
from __future__ import annotations

import typing

import mongorunway

import migrations

# Required, used by Mongorunway.
version = 2


@mongorunway.migration
def upgrade() -> typing.Sequence[mongorunway.MigrationCommand]:
    return [
        migrations.AttachCollectionValidator("abc"),
    ]


@mongorunway.migration
def downgrade() -> typing.Sequence[mongorunway.MigrationCommand]:
    return [
        migrations.DetachCollectionValidator("abc"),
    ]
```

#### `__init__.py`
!!! note
    If we apply the `make_snake_case_global_alias` decorator to the commands, passing 
    the current global scope to it
    (note that by default, commands are registered in the global scope of the 
    `mongorunway.infrastructure.commands` module):
    
    ```py
    @mongorunway.make_snake_case_global_alias(obj=globals())
    class AttachCollectionValidator(mongorunway.MigrationCommand[None]):
        pass
    
    @mongorunway.make_snake_case_global_alias(obj=globals())
    class DetachCollectionValidator(mongorunway.MigrationCommand[None]):
        pass
    ```

    then we can use the commands in the following way:
    ```
    migrations.attach_collection_validator(...)
    migrations.detach_collection_validator(...)
    ```

```py
from __future__ import annotations

import logging
import typing

import mongorunway
from mongorunway.application import ux

_LOGGER: typing.Final[logging.Logger] = logging.getLogger(__name__)

awesome_validator: typing.Final[typing.Mapping[str, typing.Any]] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "_id",
            "char",
        ],
        "properties": {
            "_id": {
                "bsonType": "int",
            },
            "char": {
                "bsonType": "string",
                "minLength": 1,
            },
        },
    },
}


class AttachCollectionValidator(mongorunway.MigrationCommand[None]):
    __slots__: typing.Sequence[str] = ("collection",)

    def __init__(self, collection: str) -> None:
        self.collection = collection

    def execute(self, ctx: mongorunway.MigrationContext) -> None:
        collection = ctx.database.get_collection(self.collection)
        validator = collection.options().get("validator")

        if validator != awesome_validator:
            _LOGGER.info("Undefined validator found, removing...")

        ctx.database.command(
            "collMod",
            collection.name,
            validationLevel=ux.ValidationLevel.STRICT,
            validationAction=ux.ValidationAction.ERROR,
            validator=awesome_validator,
        )

        _LOGGER.info(
            "Awesome schema validator successfully attached to '%s' collection.",
            collection.name,
        )


class DetachCollectionValidator(mongorunway.MigrationCommand[None]):
    __slots__: typing.Sequence[str] = ("collection",)

    def __init__(self, collection: str) -> None:
        self.collection = collection

    def execute(self, ctx: mongorunway.MigrationContext) -> None:
        collection = ctx.database.get_collection(self.collection)
        validator = collection.options().get("validator")

        _LOGGER.info("Schema validation is disabled, checking for validators...")
        if validator == awesome_validator:
            collection.database.command(
                "collMod",
                collection.name,
                validator={},
            )
            _LOGGER.info(
                "Awesome schema validator successfully detached from '%s' collection.",
                collection.name,
            )
```

#### `mongorunway.yaml`
```yaml
mongorunway:
  filesystem:
    scripts_dir: migrations

  applications:
    test:
      app_client:
        host: localhost
        port: 27017
      app_database: TestDatabase
      app_repository:
        collection: migrations
```

## Use Case

In this section, we will consider a specific case of managing migration processes.

### Downgrading
```py
> mongorunway downgrade test
2023-06-11 23:51:40 - mongorunway.ux - INFO - Mongorunway loggers successfully configured.
2023-06-11 23:51:40 - mongorunway.session - INFO - Mongorunway MongoDB context successfully initialized with MongoDB session id (a18804e32b1742dc92bd64b6c09a8e9c)
2023-06-11 23:51:40 - mongorunway.ui - INFO - test: downgrading waiting migration (#2 -> #1)...
2023-06-11 23:51:40 - mongorunway.session - INFO - Mongorunway transaction context successfully initialized with Mongorunway session id (6bb50e672a464fd59f7055951fdefabd)
2023-06-11 23:51:40 - mongorunway.transactions - INFO - Beginning a transaction in MongoDB session (a18804e32b1742dc92bd64b6c09a8e9c) for (downgrade) process.
2023-06-11 23:51:40 - migrations - INFO - Schema validation is disabled, checking for validators...
2023-06-11 23:51:40 - migrations - INFO - Awesome schema validator successfully detached from 'abc' collection.
2023-06-11 23:51:40 - mongorunway.transactions - INFO - DetachCollectionValidatorCommand command successfully applied (1 of 1).
2023-06-11 23:51:40 - mongorunway.ui - INFO - test: successfully downgraded to (#1).
===========
Mongorunway
===========

Verbose mode enabled.
Successfully downgraded 1 migration(s).
Downgraded 1 migration(s) in 0.01265406608581543s.
```

### Upgrading
```py
> mongorunway upgrade test
2023-06-11 23:52:00 - mongorunway.ux - INFO - Mongorunway loggers successfully configured.
2023-06-11 23:52:00 - mongorunway.session - INFO - Mongorunway MongoDB context successfully initialized with MongoDB session id (6fd55895572f41428b1b42b971cf757a)
2023-06-11 23:52:00 - mongorunway.ui - INFO - test: upgrading waiting migration (#1 -> #2)...
2023-06-11 23:52:00 - mongorunway.session - INFO - Mongorunway transaction context successfully initialized with Mongorunway session id (851165ddab894a07a23dd7eced512dd3)
2023-06-11 23:52:00 - mongorunway.transactions - INFO - Beginning a transaction in MongoDB session (6fd55895572f41428b1b42b971cf757a) for (upgrade) process.
2023-06-11 23:52:00 - migrations - INFO - Undefined validator found, removing...
2023-06-11 23:52:00 - migrations - INFO - Awesome schema validator successfully attached to 'abc' collection.
2023-06-11 23:52:00 - mongorunway.transactions - INFO - AttachCollectionValidatorCommand command successfully applied (1 of 1).
2023-06-11 23:52:00 - mongorunway.ui - INFO - test: Successfully upgraded to (#2).
===========
Mongorunway
===========

Verbose mode enabled.
Successfully upgraded 1 migration(s).
Upgraded 1 migration(s) in 0.0130767822265625s.
```

### Verifying
```py
> mongorunway version test
2023-06-11 23:52:13 - mongorunway.ux - INFO - Mongorunway loggers successfully configured.
===========
Mongorunway
===========

Current applied version is 2 (2 of 2)
```