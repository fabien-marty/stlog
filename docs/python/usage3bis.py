from stlog import setup, getLogger, LogContext

# in the main
setup()

logger = getLogger("myloggername")

with LogContext.bind(foo="bar", foo2="123"):
    logger.info("this is a test", foo3="baz")

logger.info("this is another test", foo3="baz")
