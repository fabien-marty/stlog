from __future__ import annotations

import logging
import sys

from stlog.base import (
    rich_dump_exception_on_console,
)
from stlog.formatter import HumanFormatter, RichHumanFormatter

RICH_INSTALLED: bool = False
try:
    from rich.console import Console

    RICH_INSTALLED = True
except ImportError:
    pass


class CustomRichHandler(logging.StreamHandler):
    """A custom StreamHandler that uses Rich Console to print log records.

    If Rich is not installed or if the stream is not a terminal,
    this handler will fallback to the default StreamHandler.

    """

    def __init__(self, stream=None, **kwargs):
        super().__init__(stream=stream)
        self.console = None
        self.force_terminal = kwargs.get("force_terminal", False)
        if RICH_INSTALLED:
            # => let's make a rich console
            self.console = Console(
                file=stream if stream else sys.stderr,
                force_terminal=True if self.force_terminal else None,
                highlight=False,
            )
            if not (self.force_terminal or self.console.is_terminal):
                # Let's fallback to a basic stream handler
                self.console = None
        if self.console is None:
            # Let's default to a human formatter
            self.formatter = HumanFormatter()
        else:
            # Let's use a rich formatter
            self.formatter = RichHumanFormatter()

    def _rich_emit(self, record: logging.LogRecord):
        assert self.console is not None
        assert self.formatter is not None
        self.console.print(self.formatter.format(record))
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            assert exc_type is not None
            assert exc_value is not None
            rich_dump_exception_on_console(
                self.console, exc_type, exc_value, exc_traceback
            )

    def emit(self, record: logging.LogRecord):
        if self.console is None or self.formatter is None:
            return super().emit(record)
        else:
            return self._rich_emit(record)
