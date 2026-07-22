from stlog import setup, getLogger

# in the main
setup()

logger = getLogger("myloggername")

with logger.context.bind(foo="bar", foo2="123"):
    logger.info("this is a test", foo3="baz")

logger.info("this is another test", foo3="baz")
