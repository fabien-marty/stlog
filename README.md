
 <!-- WARNING: generated from README.md.j2, do not modify this file manually but modify README.md.j2 instead
      and execute 'poetry run invoke readme' to regenerate this README.md file -->

 # stlog

![Python Badge](https://raw.githubusercontent.com/fabien-marty/common/refs/heads/main/badges/python38plus.svg)
[![UV Badge](https://raw.githubusercontent.com/fabien-marty/common/refs/heads/main/badges/uv.svg)](https://docs.astral.sh/uv/)
[![Task Badge](https://raw.githubusercontent.com/fabien-marty/common/refs/heads/main/badges/task.svg)](https://taskfile.dev/)
[![Mergify Badge](https://raw.githubusercontent.com/fabien-marty/common/refs/heads/main/badges/mergify.svg)](https://mergify.com/)
[![Renovate Badge](https://raw.githubusercontent.com/fabien-marty/common/refs/heads/main/badges/renovate.svg)](https://docs.renovatebot.com/)
[![MIT Licensed](https://raw.githubusercontent.com/fabien-marty/common/refs/heads/main/badges/mit.svg)](https://en.wikipedia.org/wiki/MIT_License)

[Full documentation](https://fabien-marty.github.io/stlog/)

<!--intro-start-->

## What is it?

**ST**andard **ST**ructured **LOG** (`stlog`) is Python 3.7+ [structured logging](#structured) library:

- built on [standard python logging](https://docs.python.org/3/library/logging.html) and [contextvars](https://docs.python.org/3/library/contextvars.html)
- very easy to configure with "good/opinionated" default values
- which produces great output **for both humans and machines**
- which believes in [Twelve-Factor App](https://12factor.net/) principles about config and logs
- **dependency free** (but can use fancy stuff (colors, augmented traceback...) from [the rich library](https://github.com/Textualize/rich) *(if installed)*)

## Features

- **standard, standard, standard**: all stlog objects are built on [standard python logging](https://docs.python.org/3/library/logging.html) and are compatible with:
    - other existing handlers, formatters...
    - libraries which are using a standard logger *(and `stlog` can automatically reinject the global context in log records produced by these libraries)*
- easy shorcuts to configure your logging
- provides nice outputs **for humans AND for machines** *(you can produce both at the same time)*
- structured with 4 levels of context you can choose or combine:
    - a global one set by environment variables *(read at process start)*
    - a kind of smart global one (thanks to [contextvars](https://docs.python.org/3/library/contextvars.html))
    - a context linked to the logger object itself (defined during its building)
    - a context linked to the log message itself
- a lot of configuration you can do with environment variables (in the spirit of [Twelve-Factor App](https://12factor.net/) principles)

## Non-Features

- *"A twelve-factor app never concerns itself with routing or storage of its output stream."*
    - we are going to make an exception on this for log files
    - but we don't want to introduce complex/network outputs like syslog, elasticsearch, loki...
- standard, standard, standard: we do not want to move away from [standard python logging](https://docs.python.org/3/library/logging.html) compatibility 

## <a name="structured"></a> What is *structured logging*?

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

<!--intro-end-->

## Quickstart

<!--quickstart-start-->

### Installation

```
pip install stlog
```

### Very minimal usage

```python
import stlog

stlog.info("It works", foo="bar", x=123)
stlog.critical("Houston, we have a problem!")
 
```

Output (without `rich` library installed):

```
2023-03-29T14:48:37Z root [   INFO   ] It works {foo=bar x=123}
2023-03-29T14:48:37Z root [ CRITICAL ] Houston, we have a problem!
 
```

Output (with `rich` library installed):

![rich output](docs/python/qs0.svg)
 


### Basic usage

```python
from stlog import getLogger, setup

# Set the logging default configuration (human output on stderr)
setup()

# Get a logger
logger = getLogger(__name__)
logger.info("It works", foo="bar", x=123)
logger.critical("Houston, we have a problem!")
 
```

Output (without `rich` library installed):

```
2023-03-29T14:48:37Z __main__ [   INFO   ] It works {foo=bar x=123}
2023-03-29T14:48:37Z __main__ [ CRITICAL ] Houston, we have a problem!
 
```

Output (with `rich` library installed):

![rich output](docs/python/qs1.svg)
 

### Usage with context

```python
from stlog import LogContext, getLogger, setup

# Set the logging default configuration (human output on stderr)
setup()

# ...

# Set the (kind of) global execution context
# (thread, worker, async friendly: one context by execution)
# (for example in a wsgi/asgi middleware)
# Note: ExecutionContext is a static class, so a kind of global singleton
LogContext.reset_context()
LogContext.add(request_id="4c2383f5")
LogContext.add(client_id=456, http_method="GET")

# ... in another file/class/...

# Get a logger
logger = getLogger(__name__)
logger.info("It works", foo="bar", x=123)
logger.critical("Houston, we have a problem!")
 
```

Output (without `rich` library installed):

```
2023-03-29T14:48:37Z __main__ [   INFO   ] It works {client_id=456 foo=bar http_method=GET request_id=4c2383f5 x=123}
2023-03-29T14:48:37Z __main__ [ CRITICAL ] Houston, we have a problem! {client_id=456 http_method=GET request_id=4c2383f5}
 
```

Output (with `rich` library installed):

![rich output](docs/python/qs2.svg)
 

What about if you want to get a more parsing friendly output (for example in JSON on `stdout`) while keeping the human output on `stderr` (without any context)?

```python
import sys
from stlog import LogContext, getLogger, setup
from stlog.output import StreamOutput
from stlog.formatter import HumanFormatter, JsonFormatter

setup(
    outputs=[
        StreamOutput(
            stream=sys.stderr,
            formatter=HumanFormatter(exclude_extras_keys_fnmatchs=["*"]),
        ),
        StreamOutput(stream=sys.stdout, formatter=JsonFormatter(indent=4)),
    ]
)

# See previous example for details
LogContext.reset_context()
LogContext.add(request_id="4c2383f5")
LogContext.add(client_id=456, http_method="GET")
logger = getLogger(__name__)
logger.info("It works", foo="bar", x=123)
logger.critical("Houston, we have a problem!")
 
```

Human output (on `stderr`):

```
2023-03-29T14:48:37Z __main__ [   INFO   ] It works
2023-03-29T14:48:37Z __main__ [ CRITICAL ] Houston, we have a problem!
 
```

JSON ouput (on `stdout`) for machines:

```json
{
    "client_id": 456,
    "foo": "bar",
    "http_method": "GET",
    "level": "INFO",
    "logger": "__main__",
    "message": "It works",
    "request_id": "4c2383f5",
    "source": {
        "funcName": "<module>",
        "lineno": 21,
        "module": "qs3",
        "path": "/path/filename.py",
        "process": 6789,
        "processName": "MainProcess",
        "thread": 12345,
        "threadName": "MainThread"
    },
    "time": "2023-03-29T14:48:37Z",
    "x": 123
}
{
    "client_id": 456,
    "http_method": "GET",
    "level": "CRITICAL",
    "logger": "__main__",
    "message": "Houston, we have a problem!",
    "request_id": "4c2383f5",
    "source": {
        "funcName": "<module>",
        "lineno": 22,
        "module": "qs3",
        "path": "/path/filename.py",
        "process": 6789,
        "processName": "MainProcess",
        "thread": 12345,
        "threadName": "MainThread"
    },
    "time": "2023-03-29T14:48:37Z"
}
 
```

<!--quickstart-end-->