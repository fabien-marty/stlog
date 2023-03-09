from __future__ import annotations

import inspect
import logging
import logging.handlers
import os
import sys
import typing
from dataclasses import dataclass, field

from stlog.base import RICH_INSTALLED
from stlog.formatter import HUMAN_FORMATTER


def get_program_name() -> str:
    """Return the name of the running program."""
    return os.path.basename(inspect.stack()[-1][1])


def _get_log_file_path(
    logfile: str | None = None,
    logdir: str | None = None,
    program_name: str | None = None,
    logfile_suffix: str = ".log",
) -> str:
    ret_path = None

    if not logdir:
        ret_path = logfile

    if not ret_path and logfile and logdir:
        ret_path = os.path.join(logdir, logfile)

    if not ret_path and logdir:
        program_name = program_name or get_program_name()
        ret_path = os.path.join(logdir, program_name) + logfile_suffix

    if not ret_path:
        raise ValueError("Unable to determine log file destination")

    return ret_path


@dataclass
class Output:
    _handler: logging.Handler = field(init=False, default_factory=logging.NullHandler)
    formatter: logging.Formatter = HUMAN_FORMATTER
    level: int | None = None

    def set_handler(self, handler: logging.Handler):
        self._handler = handler
        self._handler.setFormatter(self.formatter)
        if self.level is not None:
            self._handler.setLevel(self.level)

    def get_handler(self) -> logging.Handler:
        return self._handler


@dataclass
class Stream(Output):
    stream: typing.TextIO = sys.stderr
    use_fancy_rich_output: bool | None = None

    def __post_init__(self):
        if self.use_fancy_rich_output is False:
            self.set_standard_stream_handler()
            return
        if RICH_INSTALLED:
            self.set_rich_stream_handler(
                force_terminal=self.use_fancy_rich_output is True
            )
            return
        self.set_standard_stream_handler()

    def set_standard_stream_handler(self) -> None:
        self.set_handler(logging.StreamHandler(self.stream))

    def set_rich_stream_handler(self, force_terminal: bool = False) -> None:
        from rich.console import Console
        from rich.logging import RichHandler

        c = Console(file=self.stream, force_terminal=force_terminal)
        self.set_handler(RichHandler(console=c))


@dataclass
class RichStream(Output):
    def __post_init__(self):
        from rich.logging import RichHandler

        self.set_handler(RichHandler())


@dataclass
class File(Output):
    filename: str | None = None
    directory: str | None = None
    suffix: str = ".log"
    program_name: str | None = None

    def __post_init__(self):
        logpath = _get_log_file_path(
            self.filename, self.directory, self.program_name, self.suffix
        )
        handler = logging.handlers.WatchedFileHandler(logpath)
        self.set_handler(handler)
