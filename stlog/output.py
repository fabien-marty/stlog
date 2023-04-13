from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import typing
from dataclasses import dataclass, field

from stlog.base import StLogError
from stlog.formatter import (
    HumanFormatter,
    LogFmtKVFormatter,
)
from stlog.handler import CustomRichHandler

RICH_INSTALLED: bool = False
try:
    from rich.console import Console

    RICH_INSTALLED = True
except ImportError:
    pass


def _get_default_use_rich() -> bool | None:
    tmp = os.environ.get("STLOG_USE_RICH")
    if tmp is None:
        return None
    return tmp.strip().upper() in ("1", "TRUE", "YES")


DEFAULT_USE_RICH = _get_default_use_rich()


@dataclass
class Output:
    """Abstract output base class.

    Attributes:
        formatter: the Python logging Formatter to use.
        level: python logging level specific to this output
            (None means "use the global logging level").

    """

    _handler: logging.Handler = field(init=False, default_factory=logging.NullHandler)
    formatter: logging.Formatter | None = None
    level: int | None = None

    def set_handler(
        self,
        handler: logging.Handler,
    ):
        """Configure the Python logging Handler to use."""
        self._handler = handler
        self._handler.setFormatter(self.get_formatter_or_raise())
        if self.level is not None:
            self._handler.setLevel(self.level)

    def get_handler(self) -> logging.Handler:
        """Get the configured Python logging Handler."""
        return self._handler

    def get_formatter_or_raise(self) -> logging.Formatter:
        if self.formatter is None:
            raise StLogError("formatter is not set")
        return self.formatter


@dataclass
class StreamOutput(Output):
    """Represent an output to a stream (stdout, stderr...).

    Attributes:
        stream: the stream to use (`typing.TextIO`), default to `sys.stderr`.

    """

    stream: typing.TextIO = sys.stderr

    def __post_init__(self):
        if self.formatter is None:
            self.formatter = HumanFormatter()
        self.set_handler(
            logging.StreamHandler(self.stream),
        )


@dataclass
class RichStreamOutput(StreamOutput):
    force_terminal: bool = True

    def __post_init__(self):
        if self.formatter is None:
            self.formatter = HumanFormatter(
                kvs_formatter=LogFmtKVFormatter(extras_prefix="{"),
            )
        if not RICH_INSTALLED:
            raise StLogError("Rich is not installed and RichStreamOutput is specified")
        c = Console(
            file=self.stream, force_terminal=True if self.force_terminal else None
        )
        self.set_handler(CustomRichHandler(console=c))


def make_stream_or_rich_stream_output(
    stream: typing.TextIO = sys.stderr,
    use_rich: bool | None = None,
    force_terminal: bool = False,
) -> StreamOutput:
    """FIXME

    Attributes:
        use_rich: if None, use [rich output](https://github.com/Textualize/rich/blob/master/README.md) if possible
        (rich installed and supported tty), if True/False force the usage (or not).

    """
    _use_rich: bool = False
    if use_rich is not None:
        # manual mode
        _use_rich = use_rich
    else:
        # automatic mode
        if RICH_INSTALLED:
            c = Console(file=stream)
            _use_rich = c.is_terminal
    if _use_rich:
        return RichStreamOutput(stream=stream, force_terminal=force_terminal)
    else:
        return StreamOutput(stream=stream)
