from __future__ import annotations

import logging

from stlog.base import (
    StlogError,
    rich_dump_exception_on_console,
)


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
