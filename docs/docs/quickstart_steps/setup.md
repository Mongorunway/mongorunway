# Configuring Mongorunway
**Mongorunway** configuration starts with a configuration file. Currently, Mongorunway supports the 
`.yaml` configuration file format. Therefore, you need to create a `mongorunway.yaml` file and place 
it either in the current directory or in one of the directories within the current directory. 
Let's consider the second option. The structure of your project may look like this:

```py
project/
    migrations/
        # The `__init__.py` file will be convenient for 
        # storing migration process rules in the future.
        __init__.py 
        mongorunway.yaml
```

## Configuration file

!!! warning "Object path"
    In some configuration file options, you need to provide a module path that contains the 
    name of a specific object. Most objects are imported in the `root` `__init__.py` of the 
    `mongorunway` package, which allows you to omit the full path to the implementations of 
    certain objects.
    
    **If** any errors occur with these options, you can specify the full path to the object, 
    for example, `mongorunway.domain.migration_event.StartingEvent` instead of 
    `mongorunway.StartingEvent`. 

    **Both options are valid.**

```yaml
mongorunway:

  # Required. Filesystem configuration.
  filesystem:
    
    # Required. Path to the directory that contains migration files.
    scripts_dir: project/migrations
    
    # Optional. Path to the class that implements the filename strategy 
    # interface. Default value is shown below.
    filename_strategy: mongorunway.NumericalFilenameStrategy
    
    # Optional. If set to True, the filename will be transformed according 
    # to the specified filename strategy when generating a migration file 
    # template.
    use_filename_strategy: true
  
  # Required. This section contains keys that represent the names of migration 
  # applications.
  applications:
    
    # Required. Here is the configuration of the application named 'test'. You 
    # can create multiple applications, for example, one application connects 
    # to a test database, and once its migration is successful, you can 
    # confidently migrate the same process using the main application.
    # You can use the corresponding service to check the migration status.
    test:
      
      # Required. This section contains parameters that will be passed to the 
      # pymongo.MongoClient constructor.
      app_client:
        host: localhost
        port: 27017
    
      # Required. The name of the database that will be used for migration.
      app_database: TestDatabase
    
      # Required. This section contains the configuration of the migration 
      # repository, which is used for managing migration records.
      app_repository:
        
        # Case #1 (Required/Optional): If you want to use a repository based 
        # on MongoDB, you only need to specify this parameter, which represents 
        # the collection where migrations will be stored.
        collection: migrations
        
        # Case #2 (Required/Optional): Otherwise, if you want to use your own 
        # implementation of the repository, you can pass two parameters: 
        # `reader` and `type`.
        #
        # ! It is worth noting that the `reader` implementation by default 
        # takes one argument, which is the entire configuration of the current
        # application (test). This way, you can pass your own arguments to the 
        # `reader` from the configuration file and initialize them as needed.

        # Required/Optional. Path to the class that implements the repository 
        # interface.
        type: mongorunway.MongoModelRepositoryImpl
        
        # Required/Optional. Path to the function that reads the configuration 
        # and initializes the received data from the configuration file if 
        # necessary.
        reader: mongorunway.default_mongo_repository_reader
      
      # (Required/Optional). This section contains the configuration of the 
      # migration audit log, which is used for logging the migration history.
      app_auditlog_journal:
        
        # Case #1 (Required/Optional): If you want to use an audit log based 
        # on MongoDB, you only need to specify this parameter, which represents 
        # the collection where audit log entries will be stored.
        collection: auditlog
        
        # Case #2 (Required/Optional): Otherwise, if you want to use your own 
        # implementation of the audit log, you can pass two parameters: `reader` 
        # and `type`.
        #
        # ! It is worth noting that the `reader` implementation by default takes 
        # one argument, which is the entire configuration of the current 
        # application (test). This way, you can pass your own arguments to the 
        # `reader` from the configuration file and initialize them as needed.

        # Required/Optional. Path to the class that implements the audit log 
        # interface.
        type: mongorunway.MongoAuditlogJournalImpl
        
        # Required/Optional. Path to the function that reads the configuration 
        # and initializes the received data from the configuration file if 
        # necessary.
        reader: mongorunway.default_mongo_auditlog_journal_reader
  
      # Optional. Timezone for the migration application, which is used wherever 
      # the current date is recorded (e.g., in the audit log).
      app_timezone: "UTC"
      
      # Optional. Audit log limit (int), default is None. If specified, it deletes  
      # old entries and adds new ones once the limit is reached.
      app_auditlog_limit: None
      
      # Optional. Events to which the application will subscribe.
      app_events:
        
        # Path to the class that is a subclass of the base Mongorunway event.
        mongorunway.StartingEvent:
          
          # List of paths to handler functions that will be added to the 
          # specified event.
          #
          # ! Currently, you can use the "magical" prefix `Prioritized`, 
          # which wraps the handler function in a prioritized proxy. 
          # Such handlers are processed first, compared to ordinary ones, 
          # regardless of the priority of prioritized handlers. 
          # If multiple prioritized handlers are set, they will be processed 
          # sequentially according to their priority.
          - mongorunway.sync_scripts_with_repository
          - Prioritized[1, mongorunway.recalculate_migrations_checksum]
        
        # mongorunway.ClosingEvent:
        #   - ...

      # Optional. If set to False, regardless of the audit log configuration, 
      # it will not be used. Otherwise, the audit log configuration is required.
      use_auditlog: true
      
      # Optional. If set to False, all logging handlers in the `logging` module 
      # will be disabled.
      use_logging: true
      
      # Optional. If set to False, all Mongorunway indexes will be removed from 
      # the migrations collection. Otherwise, they will be added.
      #
      # ! This parameter is only relevant if your repository is based on MongoDB.
      use_indexing: true
      
      # Optional. If set to False, Mongorunway schema validation rules will be 
      # removed from the migrations collection. Otherwise, they will be added.
      #
      # ! This parameter is only relevant if your repository is based on MongoDB.
      use_schema_validation: true
      
      # Optional. If set to False, the handling of a transaction that fails will 
      # be limited to console output. Otherwise, an exception will be raised.
      raise_on_transaction_failure: true
  
  # Optional. Mongorunway loggers configuration.
  # The default configuration is provided below.
  logging:
    version: 1
    disable_existing_loggers: false

    formatters:
      simpleFormatter:
        format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        datefmt: "%Y-%m-%d %H:%M:%S"

    handlers:
      consoleHandler:
        class: "logging.StreamHandler"
        level: "DEBUG"
        formatter: "simpleFormatter"

    loggers:
      root:
        level: "INFO"
        handlers:
          - "consoleHandler"
        propagate: 0
```

## Clean configuration file
A clean configuration file with minimal settings may look like this:

```yaml
mongorunway:
  filesystem:
    scripts_dir: project/migrations

  applications:
    test:
      app_client:
        host: localhost
        port: 27017
      app_database: TestDatabase
      app_repository:
        collection: migrations
```

## Optional optimizations
If you are using a MongoDB-based repository or need to initialize, for example, a directory 
for migrations, you can use the `init` command.

### > init
| Argument                 | Description                                |
|--------------------------|--------------------------------------------|
| `APPLICATION_NAME`       | The name of the application to initialize. |

| Option   | Description                         |
|----------|-------------------------------------|
| `--verbose-exc`    | Enable verbose output for exceptions during the init command. |
| `--scripts-dir`    | Initialize the scripts directory for the specified application. |
| `--collection` | Initialize the collection for the specified application |
| `--indexes` | Initialize the indexes for the specified application's collection. |
| `--schema-validation` | Enable schema validation for the specified application's collection. |
