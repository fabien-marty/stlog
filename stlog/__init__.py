from __future__ import annotations

from stlog.adapter import getLogger
from stlog.context import LogContext
from stlog.setup import (
    critical,
    debug,
    error,
    exception,
    fatal,
    info,
    log,
    setup,
    warn,
    warning,
)

__all__ = [
    "LogContext",
    "critical",
    "debug",
    "error",
    "exception",
    "fatal",
    "getLogger",
    "info",
    "log",
    "setup",
    "warn",
    "warning",
]
__pdoc__ = {
    "base": False,
    "adapter": False,
    "handler": False,
    "filter": False,
    "context": False,
    "warn": False,
    "fatal": False,
}
VERSION = "0.0.0"
