from stlog import setup, getLogger, ExecutionLogContext

# in the main
setup()

# somewhere (wsgi/asgi middlewares...)
ExecutionLogContext.reset_context()
ExecutionLogContext.add(request_id=15843224, http_method="GET", authenticated=True)

# elsewhere
getLogger("myloggername").info("this is a test")
