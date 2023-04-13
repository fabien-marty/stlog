from __future__ import annotations

import datetime
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
logger = getLogger(__name__, foo="bar")
logger.info("It works", foo2="bar", fabien=datetime.datetime.now())
