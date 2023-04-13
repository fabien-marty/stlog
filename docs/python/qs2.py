from __future__ import annotations

from stlog import ExecutionLogContext, getLogger, setup

# Set the logging default configuration (human output on stderr)
setup()

# ...

# Set the (kind of) global execution context
# (thread, worker, async friendly: one context by execution)
# (for example in a wsgi/asgi middleware)
# Note: ExecutionContext is a static class, so a kind of global singleton
ExecutionLogContext.reset_context()
ExecutionLogContext.add(request_id="4c2383f5")
ExecutionLogContext.add(client_id=456, http_method="GET")

# ... in another file/class/...

# Get a logger
logger = getLogger(__name__)
logger.info("It works", foo="bar", x=123)
logger.critical("Houston, we have a problem!")
