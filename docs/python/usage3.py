from stlog import setup, getLogger, LogContext

# in the main
setup()

# somewhere (wsgi/asgi middlewares...)
LogContext.reset_context()
LogContext.add(request_id=15843224, http_method="GET", authenticated=True)

# elsewhere
getLogger("myloggername").info("this is a test")
