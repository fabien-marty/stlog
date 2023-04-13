from __future__ import annotations

from stlog import getLogger, setup

# Set the logging default configuration (human output on stderr)
setup()

# Get a logger
logger = getLogger(__name__)
logger.info("It works", foo="bar", x=123)
logger.critical("Houston, we have a problem!")
