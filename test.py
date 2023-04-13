from __future__ import annotations

import logging

from standard_structlog import formatter, getLogger, output, setup

setup(
    level=logging.INFO,
    outputs=(output.Stream(formatter=formatter.DATADOG_FORMATTER),),
)

logger = getLogger(__name__)
logger.reset_context()
logger.add_to_context(bar="foo")
logger.add_to_context(y=456)
logger.info("It works", foo="bar", x=123)

with logger.bind(bar="wooooo"):
    logger.info("It works (binded)", foo="bar", x=123)

logger.info("It works again", foo="bar", x=123)
