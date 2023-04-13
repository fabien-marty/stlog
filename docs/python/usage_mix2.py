import stlog
import logging

# setup
stlog.setup(reinject_context_in_standard_logging=False)

# add some global context
stlog.LogContext.reset_context()
stlog.LogContext.add(request_id=123456, is_authenticated=True, http_method="GET")

# Let's make 2 loggers: a stlog one and a standard one
standard_logger = logging.getLogger()
stlog_logger = stlog.getLogger()

# Let's use them
standard_logger.warning("this is a warning from the standard logger")
stlog_logger.critical(
    "this is a critical from stlog_logger with some extra context", xtra=123
)
