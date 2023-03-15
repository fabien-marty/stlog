from __future__ import annotations

import inspect
import os
from dataclasses import dataclass, field
from typing import Any

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


def check_json_types_or_raise(to_check: Any) -> None:
    if to_check is None:
        return
    if not isinstance(to_check, (dict, list, bool, str, int, float, bool)):
        raise StLogError(
            "to_check should be a dict/list/bool/str/int/float/bool/None, found %s"
            % type(to_check)
        )
    if isinstance(to_check, list):
        for item in to_check:
            check_json_types_or_raise(item)
    elif isinstance(to_check, dict):
        for key, value in to_check.items():
            if not isinstance(key, str):
                raise StLogError("dict keys should be str, found %s" % type(key))
            check_json_types_or_raise(value)
