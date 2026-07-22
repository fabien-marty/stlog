from stlog import setup, getLogger

# in the main
setup()

logger = getLogger("myloggername")

# somewhere (wsgi/asgi middlewares...)
logger.context.reset_context()
logger.context.add(request_id=15843224, http_method="GET", authenticated=True)

# elsewhere
logger.info("this is a test")
