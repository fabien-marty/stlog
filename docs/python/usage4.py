from stlog import setup, getLogger

# Set default configuration
setup()

# Get a logger with some context
my_logger = getLogger("myloggername", request="foo", id=123456)

# log something
my_logger.warning("this is a warning")

# log something with some extra context
my_logger.critical("this is a critical", xtr="foobar")
