# Custom event handlers case

Mongorunway provides a basic set of handlers located in the 
`mongorunway.infrastructure.event_handlers` module, but you can 
also create your own handlers.

!!! warning "Event type annotation"
    To create an event handler, you need to specify the event type annotation 
    in the `event` parameter to which the handler should be added.

## Project structure
```
project/
    migrations/
        __init__.py
        mongorunway.yaml
        # Your migration files...
```

### `__init__.py`
```py
import mongorunway

def on_app_start(event: mongorunway.StartingEvent) -> None:
    print(f"{event.application.name!r} app successfully started.")

def on_app_close(event: mongorunway.ClosingEvent) -> None:
    print(f"{event.application.name!r} app successfully closed.")
```

### `mongorunway.yaml`
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
      app_events:
        mongorunway.StartingEvent:
          - migrations.on_app_start
        mongorunway.ClosingEvent:
          - migrations.on_app_close
```

## Conclusion
Furthermore, upon each application creation, events will be dispatched and their 
corresponding handlers will be invoked.

Here's an example using the Mongorunway API:

`IN:`
```py
import mongorunway

app = mongorunway.create_app("test", raise_on_none=True, verbose_exc=True)
print(app.session.get_current_version())
```

`OUT:`
```py
'test' app successfully started.
None  # <- Your current version, for example
2023-06-12 16:38:59 - mongorunway.ux - INFO - Mongorunway loggers successfully configured.
'test' app successfully closed.
```
