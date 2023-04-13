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
    "setup",
    "getLogger",
    "LogContext",
    "log",
    "debug",
    "info",
    "warning",
    "warn",
    "error",
    "critical",
    "fatal",
    "exception",
]
__pdoc__ = {"base": False, "adapter": False, "handler": False, "context": False}
VERSION = "0.0.0"
