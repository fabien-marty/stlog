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
# {"message": "It works", "bar": "foo", "y": 456, "foo": "bar", "x": 123, "timestamp": "2023-02-18T12:35:50.184540+00:00", "status": "info", "logger": {"name": "__main__"}}

with logger.bind(bar="wooooo"):
    logger.info("It works (binded)", foo="bar", x=123)
    # {"message": "It works (binded)", "bar": "wooooo", "y": 456, "foo": "bar", "x": 123, "timestamp": "2023-02-18T12:35:50.184698+00:00", "status": "info", "logger": {"name": "__main__"}}

logger.info("It works again", foo="bar", x=123)
# {"message": "It works again", "bar": "foo", "y": 456, "foo": "bar", "x": 123, "timestamp": "2023-02-18T12:35:50.184772+00:00", "status": "info", "logger": {"name": "__main__"}}
