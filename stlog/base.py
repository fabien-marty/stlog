from __future__ import annotations

import inspect
import os
from dataclasses import dataclass, field

STLOG_EXTRA_KEY = "_stlog_extra"
RICH_INSTALLED = False
try:
    from rich.console import Console  # noqa: F401

    RICH_INSTALLED = True
except ImportError:
    pass


class StLogError(Exception):
    pass


@dataclass
class GlobalLoggingConfig:
    program_name: str = field(
        default_factory=lambda: os.path.basename(inspect.stack()[-1][1])
    )


GLOBAL_LOGGING_CONFIG = GlobalLoggingConfig()

# skip natural LogRecord attributes
# http://docs.python.org/library/logging.html#logrecord-attributes
# Stolen from https://github.com/madzak/python-json-logger/blob/master/src/pythonjsonlogger/jsonlogger.py
RESERVED_ATTRS: tuple[str, ...] = (
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
)
