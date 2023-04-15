from __future__ import annotations

import logging

from stlog.base import (
    RESERVED_ATTRS,
    STLOG_EXTRA_KEY,
    StlogError,
    rich_dump_exception_on_console,
)
from stlog.context import LogContext


class ContextReinjectHandlerWrapper(logging.Handler):
    """Logging Handler (built as a wrapper/adapter of another handler) to reinject `stlog.LogContext`
    content in log records (if they weren't sent by `stlog` special loggers)."""

    def __init__(
        self,
        *,
        wrapped: logging.Handler,
        read_extra_kwarg_from_standard_logging: bool = False,
    ):
        self._wrapped = wrapped
        self.read_extra_kwarg_from_standard_logging = (
            read_extra_kwarg_from_standard_logging
        )

    def handle(self, record: logging.LogRecord):
        if not hasattr(record, STLOG_EXTRA_KEY):
            # the context is not already injected in record
            # (this log didn't pass by stlog ContextVarsAdapter)
            # => let's fix that
            new_kwargs = LogContext._get()
            extra_keys: set[str] = getattr(record, STLOG_EXTRA_KEY, set())
            for k, v in new_kwargs.items():
                setattr(record, k, v)
                extra_keys.add(k)
            if self.read_extra_kwarg_from_standard_logging:
                # try to find special keys set by extra kwargs in
                # standard python logging
                for k in vars(record).keys():
                    if k not in RESERVED_ATTRS:
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
        if self.formatter is None:
            raise StlogError("no formatted set")
        self.console.print(self.formatter.format(record))
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            assert exc_type is not None
            assert exc_value is not None
            rich_dump_exception_on_console(
                self.console, exc_type, exc_value, exc_traceback
            )
