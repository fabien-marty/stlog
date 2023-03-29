from __future__ import annotations

import datetime

from stlog import ExecutionLogContext, getLogger, setup

# setup (globally)
setup(level="DEBUG")

# set the (kind of) global execution context (thread, worker, async friendly: one context by execution)
# (for example in a django middleware, ExecutionContext is a static class)
ExecutionLogContext.reset_context()
ExecutionLogContext.add(bar="foo")
ExecutionLogContext.add(y=456)

# from a view, import a logger and log with custom extra kv
logger = getLogger(__name__, foo="bar")
logger.debug("It works", foo2="bar", fabien=datetime.datetime.now())
logger.info("It works", foo2="bar", fabien=datetime.datetime.now())
logger.warning("It doestn't work", foo2="bar", fabien=datetime.datetime.now())
logger.critical("Bigre", foo2="bar", fabien=datetime.datetime.now())
logger.error("Bigre", foo2="bar", fabien=datetime.datetime.now())
