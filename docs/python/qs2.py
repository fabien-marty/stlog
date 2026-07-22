from stlog import LogContext, getLogger, setup

# Set the logging default configuration (human output on stderr)
setup()

# Get a logger
logger = getLogger(__name__)

# ...

# Set the (kind of) global execution context
# (thread, worker, async friendly: one context by execution)
# (for example in a wsgi/asgi middleware)

# You can do it through the logger with its `context` attribute (recommended):
logger.context.reset_context()
logger.context.add(request_id="4c2383f5")

# ...or through the LogContext static class directly (both are equivalent,
# logger.context *is* the LogContext static class):
LogContext.add(client_id=456, http_method="GET")

# ... in another file/class/...

logger.info("It works", foo="bar", x=123)
logger.critical("Houston, we have a problem!")
