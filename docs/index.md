# Home

## What is it?

**ST**andard **ST**ructured **LOG** Python 3.7+ logging library built on [standard python logging](https://docs.python.org/3/library/logging.html) and [contextvars](https://docs.python.org/3/library/contextvars.html) which produces great output for humans and for machines.

This library believes in (Twelve-Factor App)[https://12factor.net/] principles about config and logs.

The library is **dependency free** but:

- borrows plenty of ideas and code from [daiquiri](https://github.com/Mergifyio/daiquiri) library (thanks to [Mergify](https://mergify.com/) and [Julien DANJOU](https://julien.danjou.info/).
- borrows some code from [python-json-logger](https://github.com/madzak/python-json-logger) (thanks to [Zakaria ZAJAC](https://github.com/madzak))
- can use fancy stuff (colors, augmented traceback...) from the [rich library](https://github.com/Textualize/rich) *(only if installed)*

## Features

- standard, standard, standard: all stlog objects are built on [standard python logging](https://docs.python.org/3/library/logging.html) and are compatible with other existing handlers, formatters... or libraries which are using a standard logger
- easy shorcuts to configure your logging
- provides nice outputs for humans and for machines (you can produce both at the same time)
- structured with 3 levels of context you can choose or combine:
    - a kind of global one (thanks to [contextvars](https://docs.python.org/3/library/contextvars.html)
    - a context linked to the logger object itself (defined during its building)
    - a context linked to the log message itself
- be able to reinject the global context in log records produced by libraries which don't use `stlog` explicitely
- a lot of configuration you can do with environment variables (in the spirit of (Twelve-Factor App)[https://12factor.net/] principles)

## Non-Features

- "A twelve-factor app never concerns itself with routing or storage of its output stream." 
    - we make an exception on this for log files
    - but we don't want to introduce complex/network outputs like syslog, elasticsearch, loki...
- standard, standard, standard: we do not want to move away from [standard python logging](https://docs.python.org/3/library/logging.html) compatibility 

## What is *structured logging*?

> Structured logging is a technique used in software development to produce log messages that are more easily parsed and analyzed by machines. 
> Unlike traditional logging, which typically consists of free-form text messages, structured logging uses a well-defined format that includes
> named fields with specific data types.
> 
> The benefits of structured logging are many. By using a standard format, it becomes easier to automate the processing and analysis of logs.
> This can help with tasks like troubleshooting issues, identifying patterns, and monitoring system performance. It can also make it easier
> to integrate logs with other systems, such as monitoring and alerting tools.
> 
> Some common formats for structured logging include JSON, XML, and key-value pairs. In each case, the format includes a set of fields that provide information about the log message, such as the severity level, timestamp, source of the message, and any relevant metadata.
> 
> Structured logging is becoming increasingly popular as more developers recognize its benefits. Many logging frameworks and libraries now include support for structured logging, making it easier for developers to adopt the technique in their own projects.
>
> (thanks to ChatGPT)

## Why a new library and why not using [structlog](https://www.structlog.org)?

[structlog](https://www.structlog.org) is a "non standard" library (with some kind of non-perfect adapters with the standard logging system).
It's clearly a very clever piece of code but we prefer to keep 

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
logger.critical("Houston, we have a problem!")

# Output:
# 2023-03-17T08:59:09Z [INFO]     __main__#1716617: It works  [http_method: GET] [x: 123] [client_id: 456] [request_id: 4c2383f5] [foo: bar]
# 2023-03-17T09:01:30Z [CRITICAL] __main__#1716617: Houston, we have a problem!  [http_method: GET] [client_id: 456] [request_id: 4c2383f5]
```

What about if you want to get a more parsing friendly output (for example in JSON on `stdout`) while keeping the human output on `stderr` (without any context)?

```python

from stlog import ExecutionLogContext, getLogger, setup
from stlog.output import Stream
from stlog.formatter import HumanFormatter, JsonFormatter

setup(
    outputs=[
        Stream(stream=sys.stderr, formatter=HumanFormatter(exclude_extras_keys_fnmatchs=["*"])),
        Stream(stream=sys.stdout, formatter=JsonFormatter())
    ]
)
```

## Roadmap

- [ ] add `file` outputs
- [ ] add `logfmt` formatter
