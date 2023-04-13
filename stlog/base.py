from __future__ import annotations

import logging
from dataclasses import dataclass

STLOG_MANAGED_KEY = "_stdlog_managed"
RICH_INSTALLED = False
try:
    from rich.console import Console  # noqa: F401

    RICH_INSTALLED = True
except ImportError:
    pass
STLOG_EXTRA_KEYS_KEY = "_stlog_extra_keys"


@dataclass
class GlobalLoggingConfig:
    program_name: str | None = None
    reinject_context_in_standard_logging: bool = True


# Lightly adapter from https://github.com/Mergifyio/daiquiri/blob/main/daiquiri/formatter.py
class ExtrasLogRecord(logging.LogRecord):
    extras_prefix: str
    extras_suffix: str
    extras: str
    slevel_name: str
    _stlog_extra_keys: set[str]


GLOBAL_LOGGING_CONFIG = GlobalLoggingConfig()
