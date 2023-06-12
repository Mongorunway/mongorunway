# Using Mongorunway
## Introduction to usage

So, we have configured our minimal configuration file, and now it looks as follows:

```yaml
mongorunway:
  filesystem:
    scripts_dir: project/mongorunway

  applications:
    test:
      app_client:
        host: localhost
        port: 27017
      app_database: TestDatabase
      app_repository:
        collection: migrations
```

Mongorunway provides the following list of commands:

```
Usage: mongorunway [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.
 
Commands:
  auditlog           Display the audit log entries for the specified...
  check-files        Check the integrity of files in the specified...
  create-template    Create a migration template for the specified...
  downgrade          Downgrade the specified application.
  init               Initialize the specified application for migration.
  refresh            Refreshes the specified application.
  refresh-checksums  Refresh the checksums of files in the specified...
  safe-remove        Safely removes a migration from the specified...
  safe-remove-all    Safely removes all migrations from the specified...
  status             Display the migration status for the specified...
  upgrade            Upgrade the specified application.
  version            Display the version information for the specified...
  walk               Walk through the specified application.
```

Next, let's proceed with a step-by-step breakdown of the functionality.

## #1 Creating migration files

The next thing we need to do is create migration files. To do this, we can use the command 
`create-template` or create the file manually. Let's explore the first option:

```bash
mongorunway create-template test --name create_abc_collection --version 1
```

Where the `-n,--name` option is required and represents the name of the migration file, and the 
`-v,--version` option is optional and represents the migration version.

!!! note
    The --version option must be sequential. For example, if the version of the last migration is 
    2, then the version passed to this option should only be 3; otherwise, an error will be raised.

A migration file was created in the migrations directory with a transformed name 
(`001_create_abc_collection.py`, by default set to `NumericalFilenameStrategy`):

```
project/
    mongorunway/
        __init__.py 
        001_create_abc_collection.py
        mongorunway.yaml     
```

??? example "Show migration file source"
    ```py
    from __future__ import annotations
    
    import typing
    
    import mongorunway
    
    # Required, used by Mongorunway.
    version = 1
    
    
    @mongorunway.migration
    def upgrade() -> typing.List[mongorunway.MigrationCommand]:
        return []
    
    
    @mongorunway.migration
    def downgrade() -> typing.List[mongorunway.MigrationCommand]:
        return []
    ```

## #2 Modifying the migration file

Let's make sure that the content of the migration file matches its name by adding commands.
!!! info
    To add a description to the migration, include documentation in the migration module.

??? example "Show refactored migration file source"
    ```py
    from __future__ import annotations
    
    import typing
    
    import mongorunway
    
    # Required, used by Mongorunway.
    version = 1
    
    
    @mongorunway.migration
    def upgrade() -> typing.List[mongorunway.MigrationCommand]:
        return [
            mongorunway.create_collection("abc"),
        ]
    
    
    @mongorunway.migration
    def downgrade() -> typing.List[mongorunway.MigrationCommand]:
        return [
            mongorunway.drop_collection("abc"),
        ]
    ```

### Command Aliases
Here it is worth noting that `create_collection` and `drop_collection` are aliases that have been 
injected into the global scope of the **mongorunway.infrastructure.commands** module using the 
**make_snake_case_global_alias** decorator. For a more explicit implementation, you can use the 
direct implementation of commands as classes `CreateCollection` and `DropCollection`.

## #3 Updating the current state
To update the current state of migrations (synchronize recently created migration files with 
the repository), you can use the `refresh` command:

```bash
mongorunway refresh test
```

| Argument             | Description                         |
|----------------------|-------------------------------------|
| `APPLICATION_NAME` | Name of the application to refresh. |

| Option              | Is Flag | Description                                                      |
|---------------------|---------|------------------------------------------------------------------|
| `--verbose-exc`     | True   | Enable verbose output for exceptions during the refresh command. |

??? example "Expand example output"
    ```py
    > mongorunway refresh test
    2023-06-11 01:17:53 - mongorunway.ux - INFO - Mongorunway loggers successfully configured.
    2023-06-11 01:17:53 - mongorunway.ux - INFO - sync_scripts_with_repository: migration '001_create_abc_collection' with version 1 was synced and successfully append to pending.
    ===========
    Mongorunway
    ===========
    
    '001_create_abc_collection' migrations was successfully synced.
    ```

## #4 Managing migration processes
There are currently three commands available to manage migration processes: `downgrade`, 
`upgrade`, and `walk`.

### > downgrade
This command allows you to downgrade the specified application using the
given expression or additional arguments. Optionally, you can enable verbose
output or verbose output for exceptions during the downgrade process.

**Supported expressions:** `-?\d+ | - | all `

!!! note
    To prevent click from interpreting negative numbers as options, you need to precede the 
    number with --. See the example output below (Expand example output).

??? example "Expand Example"
    ```
    mongorunway downgrade test -1
    mongorunway downgrade test 1
    mongorunway downgrade test all
    mongorunway downgrade test -
    ```

| Argument             | Description                         |
|----------------------|-------------------------------------|
| `APPLICATION_NAME` | The name of the application to downgrade. |
| `EXPRESSION`, optional       | An optional expression or additional argument for the downgrade command. |

| Option              | Is Flag | Description                                                      |
|---------------------|---------|------------------------------------------------------------------|
| `--verbose-exc`     | True   | Enable verbose output for exceptions during the downgrade command. |

??? example "Expand example output"
    ```py
    > mongorunway downgrade test -- -1
    2023-06-10 23:35:56 - mongorunway.ux - INFO - Mongorunway loggers successfully configured.
    2023-06-10 23:35:56 - mongorunway.session - INFO - Mongorunway MongoDB context successfully initialized with MongoDB session id (ca795db9ff034582b05847faf480aae9)
    2023-06-10 23:35:56 - mongorunway.ui - INFO - test: downgrading waiting migration (#1 -> #None)...
    2023-06-10 23:35:56 - mongorunway.session - INFO - Mongorunway transaction context successfully initialized with Mongorunway session id (0710ebfd1c414d34bbe6f62730a9c36d)
    2023-06-10 23:35:56 - mongorunway.transactions - INFO - Beginning a transaction in MongoDB session (ca795db9ff034582b05847faf480aae9) for (downgrade) process.
    2023-06-10 23:35:56 - mongorunway.transactions - INFO - DropCollection command successfully applied (1 of 1).
    2023-06-10 23:35:56 - mongorunway.ui - INFO - test: successfully downgraded to (#None).
    ===========
    Mongorunway
    ===========
    
    Verbose mode enabled.
    Successfully downgraded 1 migration(s).
    Downgraded 1 migration(s) in 0.0055162906646728516s.
    ```

### > upgrade
This command allows you to upgrade the specified application using the
given expression or additional arguments. Optionally, you can enable
verbose output or verbose output for exceptions during the upgrade process.

**Supported expressions:** `+?\d+ | + | all `
??? example "Expand Example"
    ```
    mongorunway upgrade test +1
    mongorunway upgrade test 1
    mongorunway upgrade test all
    mongorunway upgrade test +
    ```

| Argument               | Description                         |
|------------------------|-------------------------------------|
| `APPLICATION_NAME`     | The name of the application to upgrade. |
| `EXPRESSION`, optional | An optional expression or additional argument for the upgrade command. |

| Option              | Is Flag | Description                                                      |
|---------------------|---------|------------------------------------------------------------------|
| `--verbose-exc`     | True   | Enable verbose output for exceptions during the upgrade command. |

??? example "Expand example output"
    ```py
    > mongorunway upgrade test +1    
    2023-06-10 23:36:16 - mongorunway.ux - INFO - Mongorunway loggers successfully configured.
    2023-06-10 23:36:16 - mongorunway.session - INFO - Mongorunway MongoDB context successfully initialized with MongoDB session id (ef6ece8e7c97436cbf691f1d91fc33bc)
    2023-06-10 23:36:16 - mongorunway.ui - INFO - test: upgrading waiting migration (#None -> #1)...
    2023-06-10 23:36:16 - mongorunway.session - INFO - Mongorunway transaction context successfully initialized with Mongorunway session id (0659cda9dc464ffd9b8169b090e38195)
    2023-06-10 23:36:16 - mongorunway.transactions - INFO - Beginning a transaction in MongoDB session (ef6ece8e7c97436cbf691f1d91fc33bc) for (upgrade) process.
    2023-06-10 23:36:16 - mongorunway.transactions - INFO - CreateCollection command successfully applied (1 of 1).
    2023-06-10 23:36:16 - mongorunway.ui - INFO - test: Successfully upgraded to (#1).
    ===========
    Mongorunway
    ===========
    
    Verbose mode enabled.
    10003 Successfully upgraded 1 migration(s).
    Upgraded 1 migration(s) in 0.012265443801879883s.
    ```

### > walk
This command allows you to perform a walk operation on the specified
application using the given expression or additional arguments. The
walk operation enables you to traverse the application's structure or
perform specific actions.

Optionally, you can enable verbose output or verbose output for exceptions
during the walk process.

**Supported expressions:** `[+-]?\d+ | + | - `
??? example "Expand Example"
    ```
    mongorunway walk test +1
    mongorunway walk test -1
    mongorunway walk test +
    mongorunway walk test -
    ```

| Argument              | Description                                             |
|-----------------------|---------------------------------------------------------|
| `APPLICATION_NAME`    | The name of the application for the walk command.       |
| `EXPRESSION`          | Expression or additional argument for the walk command. |

| Option                | Is Flag | Description                                                        |
| --------------------- |---------|--------------------------------------------------------------------|
| `--verbose-exc`       | True   | Enable verbose output for exceptions during the walk command.             |

??? example "Expand example output"
    ```py
    > mongorunway walk test -
    2023-06-10 23:32:57 - mongorunway.ux - INFO - Mongorunway loggers successfully configured.
    2023-06-10 23:32:57 - mongorunway.session - INFO - Mongorunway MongoDB context successfully initialized with MongoDB session id (766a81ff90574c23ab950d13bd1a3cb5)
    2023-06-10 23:32:57 - mongorunway.ui - INFO - test: downgrading waiting migration (#1 -> #None)...
    2023-06-10 23:32:57 - mongorunway.session - INFO - Mongorunway transaction context successfully initialized with Mongorunway session id (cfa37d128911401198fddab4741ea8a7)
    2023-06-10 23:32:57 - mongorunway.transactions - INFO - Beginning a transaction in MongoDB session (766a81ff90574c23ab950d13bd1a3cb5) for (downgrade) process.
    2023-06-10 23:32:57 - mongorunway.transactions - INFO - DropCollection command successfully applied (1 of 1).
    2023-06-10 23:32:57 - mongorunway.ui - INFO - test: successfully downgraded to (#None).
    ===========
    Mongorunway
    ===========
    
    Verbose mode enabled.
    10003 Successfully downgraded 1 migration(s).
    Downgraded 1 migration(s) in 0.0050008296966552734s.
    ```

## #5 Verifying migration results

To retrieve the current state, there are commands such as `auditlog`, `status`, and `version`.

### > auditlog
This command allows you to view the audit log entries for the
specified application. You can filter the entries by specifying a
start and/or end timestamp or date. The maximum number of entries
displayed can be limited, and you can choose to sort the entries
in ascending order by date.

Optionally, you can enable verbose output for exceptions that may
occur during the audit log command.

!!! info 
    To enable the audit log functionality, I added the following parameters to the 
    configuration file:
    ```yaml
    mongorunway:
      # ...
      applications:
        # ...
        app_auditlog_journal:
          collection: auditlog
        use_auditlog: true
    ```

!!! note "Start, End"
    You should specify the `--start` and `--end` options in the format specified in the application 
    configuration by the **application.app_date_fmt** parameter.

| Argument                 | Description                                                             |
|--------------------------|-------------------------------------------------------------------------|
| `APPLICATION_NAME`       | The name of the application for which to display the audit log entries. |

| Option             | Is Flag      | Description                                                        |
| ------------------------ | -------|--------------------------------------------------------------------|
| `-s`, `--start`     |  False    | Start timestamp or date for filtering audit log entries.           |
| `-e`, `--end`       |  False   | End timestamp or date for filtering audit log entries.             |
| `-l`, `--limit`     |   False  | Maximum number of audit log entries to display.                    |
| `-a`, `--ascending`  |   True    | Sort the audit log entries in ascending order by date.             |
| `--verbose-exc`      |   True   | Enable verbose output for exceptions during the audit log command. |

??? example "Expand example output"
    ```py
    > mongorunway auditlog test                 
    2023-06-11 00:21:55 - mongorunway.ux - INFO - Mongorunway loggers successfully configured.
    ```

    | Date                | Is Failed  | Transaction Type   | Migration                       |
    |---------------------|------------|--------------------|---------------------------------|
    | 2023-06-10 21:21:06 | False     | UpgradeTransaction | Name: 001_create_abc_collection |
    |                     |           |                    | Version: 1                       |
    |                     |           |                    | Is applied: False               |
    |                     |           |                    |                                 |


### > status
This command allows you to view the migration status of the specified
application. It shows the history of applied migrations up to the
specified depth.

Optionally, you can enable verbose output for the status command and
verbose output for exceptions that may occur during the status check.

| Argument                 | Description                                                              |
|--------------------------|--------------------------------------------------------------------------|
| `APPLICATION_NAME`       | The name of the application for which to display the migration status. |

| Option              | Is Flag | Description                                                        |
|---------------------|---------|--------------------------------------------------------------------|
| `-d`, `--depth`     | False   | Specify the depth of the migration history to display.                    |
| `--verbose-exc`     | True   | Enable verbose output for exceptions during the status command.             |

??? example "Expand example output"
    - Case 1
    ```py
    > mongorunway status test 
    2023-06-11 00:25:04 - mongorunway.ux - INFO - Mongorunway loggers successfully configured.
    ===========
    Mongorunway
    ===========
    
    All migrations applied successfully in depth -1 (1 of 1)
    ```
    
    - Case 2
    ```py
    > mongorunway status test -d 2
    2023-06-11 00:25:42 - mongorunway.ux - INFO - Mongorunway loggers successfully configured.
    ===========
    Mongorunway
    ===========
    
    ValueError : Depth (2) cannot be more than migration files count (1).
    ```

### > version
This command allows you to view the version information of the
specified application. It shows details such as the application's
name, version number, and other relevant details.

Optionally, you can enable verbose output for the version command
to get more detailed information.

| Argument                 | Description                                                              |
|--------------------------|--------------------------------------------------------------------------|
| `APPLICATION_NAME`       | The name of the application for which to display the version information. |

| Option              | Is Flag | Description                                                        |
|---------------------|---------|--------------------------------------------------------------------|
| `--verbose-exc`     | True   | Enable verbose output for exceptions during the version command.             |

??? example "Expand example output"
    ```py
    > mongorunway version test
    2023-06-11 00:15:53 - mongorunway.ux - INFO - Mongorunway loggers successfully configured.
    ===========
    Mongorunway
    ===========
    
    Current applied version is 1 (1 of 1)
    ```


## #6 Removing migrations safely

There are two commands available for safe removal of migrations: 
`safe-remove` and `safe-remove-all` .

!!! faq "Why are they safe?"
    These methods are safe in a way that they allow you to control the process 
    of removing migrations sequentially. For example, if you are on schema version 4, 
    you will not be able to remove the schema with version 3.
    
    These methods also allow you to remove migration data both from your repository 
    and from the migrations directory.

### > safe-remove
| Argument            | Description                                           |
|---------------------|-------------------------------------------------------|
| `APPLICATION_NAME`  | The name of the application to remove migration from. |
| `MIGRATION_VERSION` | Migration version to remove.                          |

| Option              | Is Flag | Description                                                          |
|---------------------|---------|----------------------------------------------------------------------|
| `--verbose-exc`     | True   | Enable verbose output for exceptions during the safe-remove command. |

??? example "Expand example output"
    ```py
    > mongorunway safe-remove test 3
    2023-06-12 14:31:32 - mongorunway.ux - INFO - Mongorunway loggers successfully configured.
    ===========
    Mongorunway
    ===========
    
    Migration with version 3 has been successfully deleted.
    ```

### > safe-remove-all

!!! warning 
    This command deletes all files in the directory that do NOT start with an underscore (_) 
    and have the extension `.py`.

| Argument            | Description                                            |
|---------------------|--------------------------------------------------------|
| `APPLICATION_NAME`  | The name of the application to remove migrations from. |

| Option              | Is Flag | Description                                                              |
|---------------------|---------|--------------------------------------------------------------------------|
| `--verbose-exc`     | True   | Enable verbose output for exceptions during the safe-remove-all command. |

??? example "Expand example output"
    ```py
    > mongorunway safe-remove-all test
    2023-06-12 14:32:19 - mongorunway.ux - INFO - Mongorunway loggers successfully configured.
    ===========
    Mongorunway
    ===========
    
    Successfully deleted 2 migration(s).
    ```

## #7 Checking files integrity and fixing any inconsistencies

### > refresh-checksums

If your application is subscribed to a handler that compares checksums of files from the 
repository with the current state of the migration file, and it detects any inconsistencies, 
you can recalculate the checksums of modified files using the `refresh-checksums` command.

| Argument            | Description                                           |
|---------------------|-------------------------------------------------------|
| `APPLICATION_NAME`  | The name of the application to refresh checksums for. |

| Option              | Is Flag | Description                                                                |
|---------------------|---------|----------------------------------------------------------------------------|
| `--verbose-exc`  | True   | Enable verbose output for exceptions during the refresh-checksums command. |

### > check-files

If you want to monitor changes in your files, you can use the `check-files` command, which 
compares the checksums of files and displays information in the terminal in case of any 
inconsistencies.

This command also supports raising an error, which can be useful for CI 
(Continuous Integration) purposes.

| Argument            | Description                                           |
|---------------------|-------------------------------------------------------|
| `APPLICATION_NAME`  | The name of the application to refresh checksums for. |

| Option          | Is Flag | Description                                                          |
|-----------------|---------|----------------------------------------------------------------------|
| `--verbose-exc` | True   | Enable verbose output for exceptions during the check-files command. |
| `--raise-exc`   | True   | Throws an exception if a mismatch is found.                          |
