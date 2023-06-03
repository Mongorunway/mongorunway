r"""
Example of rules that are invoked before a specific migration process.
"""
from __future__ import annotations

__all__: typing.Sequence[str] = ("RequiredFieldRule", "RequiredCollRule")

import typing

import mongorunway

beautiful_collection = "test_col"
beautiful_field = "beautiful_field"


class RequiredFieldRule(mongorunway.AbstractMigrationBusinessRule):
    def __init__(self) -> None:
        # Now, before executing the checks of this rule, both
        # `RequiredCollRule` and all rules on which `RequiredCollRule`
        # depends will be recursively validated.
        super().__init__(depends_on=[RequiredCollRule()])

    def check_is_broken(self, ctx: mongorunway.MigrationContext) -> bool:
        r"""Checks if all documents have a certain field."""
        collection = ctx.database.get_collection(beautiful_collection)
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

            if beautiful_field not in document:
                # Checks if a specific field exists in the collection document.
                return True

            count += 1

    def render_broken_rule(self) -> str:
        return (
            super().render_broken_rule()
            + " "
            + "There are not documents or document does not have 'required_field' field."
        )


class RequiredCollRule(mongorunway.AbstractMigrationBusinessRule):
    def check_is_broken(self, ctx: mongorunway.MigrationContext) -> bool:
        r"""Checks if a specific collection exists in the current database."""
        return beautiful_collection not in ctx.database.list_collection_names()

    def render_broken_rule(self) -> str:
        return (
            super().render_broken_rule()
            + " "
            + f"Collection {beautiful_collection}' is not created."
        )
