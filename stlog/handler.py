from __future__ import annotations

import logging

from stlog.base import (
    STLOG_EXTRA_KEY,
)
from stlog.context import ExecutionLogContext
from stlog.formatter import HumanFormatter


class ContextReinjectHandlerWrapper(logging.Handler):
    """Logging Handler (built as a wrapper/adapter of another handler) to reinject `stlog.ExecutionLogContext`
    content in log records (if they weren't sent by `stlog` special loggers)."""

    def __init__(self, *, wrapped: logging.Handler):
        self._wrapped = wrapped

    def handle(self, record):
        if not hasattr(record, STLOG_EXTRA_KEY):
            # the context is not already injected in record
            # (this log didn't pass by stlog ContextVarsAdapter)
            # => let's fix that
            new_kwargs = ExecutionLogContext._get()
            extra_keys: set[str] = getattr(record, STLOG_EXTRA_KEY, set())
            for k, v in new_kwargs.items():
                setattr(record, k, v)
                extra_keys.add(k)
            setattr(record, STLOG_EXTRA_KEY, extra_keys)
        self._wrapped.handle(record)

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        # Wraps other calls to real handler
        return getattr(self._wrapped, attr)


class CustomRichHandler(logging.Handler):
    def __init__(self, console, level: int = logging.NOTSET, **kwargs):
        self.console = console
        super().__init__(level=level)

    def emit(self, record: logging.LogRecord):
        from rich.table import Table
        from rich.text import Text

        lll = record.levelname.lower()
        llu = lll.upper()
        name = record.name
        assert isinstance(self.formatter, HumanFormatter)
        ts = self.formatter.formatTime(record, datefmt=self.formatter.datefmt)
        msg = record.getMessage()
        extra = self.formatter._make_extras_string(record)
        if lll in ["notset", "debug", "info", "warning", "error", "critical"]:
            ls = "logging.level.%s" % lll
        else:
            ls = "none"
        output = Table(show_header=False, expand=True, box=None, padding=(0, 1, 0, 0))
        output.add_column(style="log.time")
        output.add_column(width=10, justify="center")
        output.add_column(justify="center")
        output.add_column(ratio=1)
        row = []
        row.append(Text(ts))
        row.append(Text(llu, style=ls))
        row.append(Text(name, style="bold"))
        row.append(Text(msg))
        output.add_row(*row)
        if extra != "":
            output.add_row("", "", "", Text(extra, style="repr.attrib_name"))
        self.console.print(output)
