# Custom rules case
Mongorunway also allows users to implement their own business rules, which act as 
validators and are invoked before a specific migration process.

!!! info
    In future versions, there are plans to add an additional method, `resolve`, to 
    the business rules interface, which would allow for correcting the collection 
    schema if the rule is violated.
    
    Currently, you can handle this manually.

## Project structure
```py
migrations/
    __init__.py
    001_create_collection_with_name_abc.py
    002_add_field_to_abc_collection.py
```

Next, we will present and discuss the implementations of the components in this 
project structure.

### `001_create_collection_with_name_abc.py`
```py
from __future__ import annotations

import typing

import mongorunway

import migrations

# Required, used by Mongorunway.
version = 1


@mongorunway.migration
def upgrade() -> typing.Sequence[mongorunway.MigrationCommand]:
    return [
        mongorunway.create_collection("abc"),
    ]


# This process will not be executed only if the 'abc' 
# collection has been deleted.
@mongorunway.migration_with_rule(migrations.CollectionRequired("abc"))
@mongorunway.migration
def downgrade() -> typing.Sequence[mongorunway.MigrationCommand]:
    return [
        mongorunway.drop_collection("abc"),
    ]
```


### `002_add_field_to_abc_collection.py`
```py
from __future__ import annotations

import typing

import mongorunway

import migrations

# Required, used by Mongorunway.
version = 2


@mongorunway.migration
def upgrade() -> typing.Sequence[mongorunway.MigrationCommand]:
    r"""Adds 'field' field to each document of the collection."""
    return [
        mongorunway.update_many({}, {"$set": {"field": ""}}),
    ]


# This process will not be executed only if the 'abc' 
# collection has been deleted or if any of the documents 
# in the collection lacks a field named 'field'.
@mongorunway.migration_with_rule(migrations.FieldRequired(field="field", collection="abc"))
@mongorunway.migration
def downgrade() -> typing.Sequence[mongorunway.MigrationCommand]:
    r"""Removes 'field' field from each document of the collection."""
    return [
        mongorunway.update_many({}, [{"$unset": ["field"]}]),
    ]
```

### `__init__.py`
```py
from __future__ import annotations

__all__: typing.Sequence[str] = ("FiledRequired", "CollectionRequired")

import typing

import mongorunway


class FiledRequired(mongorunway.AbstractMigrationBusinessRule):
    def __init__(
        self,
        collection: str,
        field: str,
    ) -> None:
        # Now, before executing the checks of this rule, both
        # `CollectionRequired` and all rules on which `CollectionRequired`
        # depends will be recursively validated.
        super().__init__(depends_on=[CollectionRequired(collection=collection)])
        self._field = field
        self._collection = collection

    def check_is_broken(self, ctx: mongorunway.MigrationContext) -> bool:
        r"""Checks if all documents have a certain field."""
        collection = ctx.database.get_collection(self._collection)
        documents = collection.find({})

        count = 0
        while True:
            try:
                document = documents.next()
            except StopIteration:
                if not count:
                    # If the collection is empty and no documents have
                    # been processed.
                    return True

                # Otherwise, all documents have been processed successfully,
                # and the rule is not violated.
                return False

            if self._field not in document:
                # Checks if a specific field exists in the collection document.
                return True

            count += 1

    def render_broken_rule(self) -> str:
        return (
            super().render_broken_rule()
            + " "
            + f"There are not documents or document does"
              f" "
              f"not have '{self._field}' field."
        )


class CollectionRequired(mongorunway.AbstractMigrationBusinessRule):
    def __init__(
        self, 
        collection: str, 
        depends_on: typing.Sequence[mongorunway.MigrationBusinessRule] = (),
    ) -> None:
        super().__init__(depends_on=depends_on)
        self._collection = collection
    
    def check_is_broken(self, ctx: mongorunway.MigrationContext) -> bool:
        r"""Checks if a specific collection exists in the current database."""
        return self._collection not in ctx.database.list_collection_names()

    def render_broken_rule(self) -> str:
        return (
            super().render_broken_rule()
            + " "
            + f"Collection {self._collection}' is not created."
        )
```