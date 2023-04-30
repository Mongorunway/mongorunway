import contextvars
import logging

logger = logging.getLogger("mongorunway")

handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger.addHandler(handler)
CLI_EXTRA_KWARGS = contextvars.ContextVar("CLI_EXTRA_KWARGS", default={})
