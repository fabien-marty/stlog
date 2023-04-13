from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import typing
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from stlog.base import GLOBAL_LOGGING_CONFIG, RICH_INSTALLED, StLogError
from stlog.formatter import (
    DEFAULT_STLOG_HUMAN_FORMAT,
    DEFAULT_STLOG_RICH_FORMAT,
    HumanFormatter,
)

if TYPE_CHECKING:
    from rich.console import Console
    from rich.logging import RichHandler


def _get_default_use_rich() -> bool | None:
    tmp = os.environ.get("STLOG_USE_RICH")
    if tmp is None:
        return None
    return tmp.strip().upper() in ("1", "TRUE", "YES")


DEFAULT_USE_RICH = _get_default_use_rich()


def _get_log_file_path(
    logfile: str | None = None,
    logdir: str | None = None,
    logfile_suffix: str = ".log",
) -> str:
    ret_path = None

    if not logdir:
        ret_path = logfile

    if not ret_path and logfile and logdir:
        ret_path = os.path.join(logdir, logfile)

    if not ret_path and logdir:
        ret_path = (
            os.path.join(logdir, GLOBAL_LOGGING_CONFIG.program_name) + logfile_suffix
        )

    if not ret_path:
        raise ValueError("Unable to determine log file destination")

    return ret_path


@dataclass
class Output:
    """Abstract output base class.

    Attributes:
        formatter: the Python logging Formatter to use.
        level: FIXME.

    """

    _handler: logging.Handler = field(init=False, default_factory=logging.NullHandler)
    formatter: logging.Formatter | None = field(default_factory=HumanFormatter)

    level: int | None = None

    def set_handler(
        self,
        handler: logging.Handler,
    ):
        """Configure the Python logging Handler to use."""
        self._handler = handler
        if self.formatter is None:
            raise StLogError("formatter is not set")
        self._handler.setFormatter(self.formatter)
        if self.level is not None:
            self._handler.setLevel(self.level)

    def get_handler(self) -> logging.Handler:
        """Get the configured Python logging Handler."""
        return self._handler


@dataclass
class Stream(Output):
    """Represent an output to a stream (stdout, stderr...).

    Attributes:
        stream: the stream to use (`typing.TextIO`), default to `sys.stderr`.
        use_fancy_rich_output: if None, use fancy rich output if possible (rich installed and supported tty),
            if True/False force the usage (or not).

    """

    stream: typing.TextIO = sys.stderr
    use_rich: bool | None = DEFAULT_USE_RICH
    _use_rich: bool = False

    def __post_init__(self):
        self._resolve_rich()
        self._set_default_formatter_if_not_set()
        self._set_stream_handler()

    def _resolve_rich(self) -> None:
        self._use_rich = False
        if self.use_rich is True:
            self._use_rich = True
        elif self._use_rich is None:
            # Automatic
            if RICH_INSTALLED:
                from rich.console import Console

                c = Console(self.stream)
                self._use_rich = c.is_terminal()

    def _set_default_formatter_if_not_set(self) -> None:
        if self.formatter is not None:
            return
        if self._use_rich:
            self.formatter = HumanFormatter(fmt=DEFAULT_STLOG_RICH_FORMAT)
        else:
            self.formatter = HumanFormatter(fmt=DEFAULT_STLOG_HUMAN_FORMAT)

    def _set_stream_handler(self) -> None:
        if self._use_rich:
            self._set_rich_stream_handler(force_terminal=self.use_rich is True)
        else:
            self._set_standard_stream_handler()

    def _set_standard_stream_handler(self) -> None:
        self.set_handler(
            logging.StreamHandler(self.stream),
        )

    def _set_rich_stream_handler(self, force_terminal: bool = False) -> None:
        from rich.console import Console

        c = Console(file=self.stream, force_terminal=force_terminal)
        self.set_handler(self._make_rich_handler(c))

    def _make_rich_handler(self, c: Console) -> RichHandler:
        from rich.logging import RichHandler

        return RichHandler(console=c, show_path=False, omit_repeated_times=False)


@dataclass
class File(Output):
    filename: str | None = None
    directory: str | None = None
    suffix: str = ".log"

    def __post_init__(self):
        logpath = _get_log_file_path(self.filename, self.directory, self.suffix)
        handler = logging.handlers.WatchedFileHandler(logpath)
        self.set_handler(handler)
