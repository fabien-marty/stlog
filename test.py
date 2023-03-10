from __future__ import annotations

import logging
import sys
import time

from stlog import ExecutionLogContext, getLogger, setup
from stlog.output import Stream

# setup (globally)
setup(
    level=logging.INFO,
    outputs=(
        Stream(
            stream=sys.stdout,
            use_fancy_rich_output=False,
        ),
        Stream(
            stream=sys.stderr,
            use_fancy_rich_output=True,
        ),
    ),
)

# set the (kind of) global execution context (thread, worker, async friendly: one context by execution)
# (for example in a django middleware, ExecutionContext is a static class)
ExecutionLogContext.reset_context()
ExecutionLogContext.add(bar="foo")
ExecutionLogContext.add(y=456)

# from a view, import a logger and log with custom extra kv
logger = getLogger(__name__)
logger.info("It works", foo="bar", x=123)
# {"message": "It works", "bar": "foo", "y": 456, "foo": "bar", "x": 123, "timestamp": "2023-02-18T12:35:50.184540+00:00", "status": "info", "logger": {"name": "__main__"}}

# we can also bind the execution context to add some kvs in a big part of the code
with ExecutionLogContext.bind(bar="wooooo"):
    logger.info("It works (binded)", foo="bar", x=123)
    # {"message": "It works (binded)", "bar": "wooooo", "y": 456, "foo": "bar", "x": 123, "timestamp": "2023-02-18T12:35:50.184698+00:00", "status": "info", "logger": {"name": "__main__"}}

logger.critical("It works again", foo="bar", x=123)
# {"message": "It works again", "bar": "foo", "y": 456, "foo": "bar", "x": 123, "timestamp": "2023-02-18T12:35:50.184772+00:00", "status": "info", "logger": {"name": "__main__"}}

ExecutionLogContext.remove("bar", "y")
logger.warning("plop")
# {"message": "plop", "timestamp": "2023-02-19T12:20:24.393459+00:00", "status": "info", "logger": {"name": "__main__"}}


time.sleep(1)

ExecutionLogContext.add(bar="foo")
ExecutionLogContext.add(y=456)
logger.info(
    """multilines
multilines"""
)

std_logger = logging.getLogger("standard")
std_logger.info("foo")

1 / 0
