from __future__ import annotations

import logging

from standard_structlog import ExecutionContext, formatter, getLogger, output, setup

# setup (globally)
setup(
    level=logging.INFO,
    outputs=(output.Stream(formatter=formatter.DATADOG_FORMATTER),),
)

# set the (kind of) global execution context (thread, worker, async friendly: one context by execution)
# (for example in a django middleware, ExecutionContext is a static class)
ExecutionContext.reset_context()
ExecutionContext.add(bar="foo")
ExecutionContext.add(y=456)

# from a view, import a logger and log with custom extra kv
logger = getLogger(__name__)
logger.info("It works", foo="bar", x=123)
# {"message": "It works", "bar": "foo", "y": 456, "foo": "bar", "x": 123, "timestamp": "2023-02-18T12:35:50.184540+00:00", "status": "info", "logger": {"name": "__main__"}}

# we can also bind the execution context to add some kvs in a big part of the code
with ExecutionContext.bind(bar="wooooo"):
    logger.info("It works (binded)", foo="bar", x=123)
    # {"message": "It works (binded)", "bar": "wooooo", "y": 456, "foo": "bar", "x": 123, "timestamp": "2023-02-18T12:35:50.184698+00:00", "status": "info", "logger": {"name": "__main__"}}

logger.info("It works again", foo="bar", x=123)
# {"message": "It works again", "bar": "foo", "y": 456, "foo": "bar", "x": 123, "timestamp": "2023-02-18T12:35:50.184772+00:00", "status": "info", "logger": {"name": "__main__"}}

ExecutionContext.remove("bar", "y")
logger.info("plop")
# {"message": "plop", "timestamp": "2023-02-19T12:20:24.393459+00:00", "status": "info", "logger": {"name": "__main__"}}
