from stlog import setup, getLogger

# Set default configuration
setup()

# Get a logger
my_logger = getLogger("myloggername")

# log something
my_logger.warning("this is a warning")
