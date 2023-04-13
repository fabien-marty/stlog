from stlog import setup, getLogger

# Set default configuration
setup(level="DEBUG")

# Get a logger
my_logger = getLogger("myloggername")

my_logger.debug("Classic example with %s", "positional arguments")
my_logger.info(
    "Example with both *args (%s, %s) and **kwargs",
    "foo",
    "bar",
    foo="bar",
    foo2="bar2",
)
try:
    1 / 0
except Exception:
    # Note: exc_info is a reserved kwargs on python standard logger
    my_logger.warning("this is a warning with exc_info=True", exc_info=True)

# Note: extra is a reserved kwargs on python standard logger
# to provide some structured logging features
# (=> we recommand to use classic **kwargs instead)
my_logger.error(
    "Using a standard extra",
    foo="bar",
    foo2="bar2",
    extra={"foo3": "bar3", "foo4": "bar4"},
)
