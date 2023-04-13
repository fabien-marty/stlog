from stlog import setup, getLogger

# Set default configuration
setup()

# Get a logger
my_logger = getLogger("myloggername")

# log something with some extra context
my_logger.critical("this is a critical", request="foo", id=123456)
