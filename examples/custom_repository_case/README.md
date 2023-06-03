# Custom Repository Case

In this case, by setting the path to your custom repository and its reader in the 
`mongorunway/mongorunway.yaml` configuration file, you can use both the **CLI** and the 
mongorunway **API**.

### API example
```py
from mongorunway import api

# The configuration file path is optional in this case, as mongorunway 
# can search for the configuration file in the current directory or in 
# the immediate subdirectories at a depth of 1 (subdirectories beyond 
# that level will not be searched).
app = api.create_app("myapp", raise_on_none=True, verbose_exc=True)
app.upgrade_once()

# You can also utilize higher-level functions from the 
# `mongorunway.application.use_cases module.` These functions provide a 
# more simplified API, and their execution is accompanied by additional 
# information, such as code execution time.
from mongorunway.application import use_cases
use_cases.upgrade("+1")
```
