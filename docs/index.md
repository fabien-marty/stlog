# Home

## What is it?

**ST**andard **ST**ructured **LOG** Python 3.7+ logging library built on [standard python logging](https://docs.python.org/3/library/logging.html) and [contextvars](https://docs.python.org/3/library/contextvars.html).

The library is **dependency free** but:

- borrows plenty of ideas and code from [daiquiri](https://github.com/Mergifyio/daiquiri) library (thanks to [Mergify](https://mergify.com/) and [Julien DANJOU](https://julien.danjou.info/).
- borrows some code from [python-json-logger](https://github.com/madzak/python-json-logger) (thanks to [Zakaria ZAJAC](https://github.com/madzak))
- can use fancy stuff (colors, augmented traceback...) from the [rich library](https://github.com/Textualize/rich) *(only if installed)*

## What is *structured logging*?

FIXME

## Why a new library and why not using [structlog](https://www.structlog.org)?

FIXME

## Quickstart

### Installation

```
pip install stlog
```

### Usage

```python
from stlog import ExecutionLogContext, getLogger, setup

# Set the logging default configuration (human output on stderr)
setup()

# ...

# Set the (kind of) global execution context
# (thread, worker, async friendly: one context by execution)
# (for example in a wsgi/asgi middleware)
# Note: ExecutionContext is a static class, so a kind of global singleton
ExecutionLogContext.reset_context()
ExecutionLogContext.add(request_id="4c2383f5")
ExecutionLogContext.add(client_id=456, http_method="GET")

# ... in another file/class/...

# Get a logger
logger = getLogger(__name__)
logger.info("It works", foo="bar", x=123)

# Output:
# 2023-03-12 21:03:51 (utc) [INFO]     __main__#1397968: It works  [foo: bar] [x: 123] [client_id: 456] [request_id: 4c2383f5] [http_method: GET]
```

What about if you want to get a more parsing friendly output (for example on `stdout`) while keeping the human output on `stderr`?

```python

from stlog import ExecutionLogContext, getLogger, setup
from stlog.output import Stream
from stlog.formatter import HumanFormatter, JsonFormatter

setup(
    outputs=[
        Stream(stream=sys.stderr, formatter=HumanFormatter()),
        Stream(stream=sys.stdout, formatter=JsonFormatter())
    ]
)
```