from __future__ import annotations

from stlog.adapter import getLogger
from stlog.context import ExecutionLogContext
from stlog.setup import setup

__all__ = [
    "setup",
    "getLogger",
    "ExecutionLogContext",
]
__pdoc__ = {"base": False, "adapter": False, "handler": False, "context": False}
VERSION = "0.0.0"
