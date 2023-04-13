from __future__ import annotations

import logging

from stlog import ExecutionLogContext, getLogger, setup
from stlog.formatter import JsonFormatter
from stlog.output import StreamOutput

# setup (globally)
setup(
    level=logging.INFO,
    outputs=(StreamOutput(formatter=JsonFormatter()),),
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


def foo():
    try:
        1 / 0
    except ZeroDivisionError:
        logger.critical("exception catched", exc_info=True)


foo()
