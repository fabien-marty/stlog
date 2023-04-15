from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import typing
from dataclasses import dataclass, field

from stlog.base import StlogError
from stlog.formatter import (
    HumanFormatter,
    RichHumanFormatter,
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
    if tmp.strip().upper() in ("NONE", "AUTO", ""):
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
        filters: list of logging Filters (or simple callables) to filter some LogRecord
            for this specific output.

    """

    _handler: logging.Handler = field(init=False, default_factory=logging.NullHandler)
    formatter: logging.Formatter | None = None
    level: int | str | None = None
    filters: typing.Iterable[
        typing.Callable[[logging.LogRecord], bool] | logging.Filter
    ] = field(default_factory=list)

    def set_handler(
        self,
        handler: logging.Handler,
    ):
        """Configure the Python logging Handler to use."""
        self._handler = handler
        self._handler.setFormatter(self.get_formatter_or_raise())
        if self.level is not None:
            self._handler.setLevel(self.level)
        for filter in self.filters:
            self._handler.addFilter(filter)

    def get_handler(self) -> logging.Handler:
        """Get the configured Python logging Handler."""
        return self._handler

    def get_formatter_or_raise(self) -> logging.Formatter:
        if self.formatter is None:
            raise StlogError("formatter is not set")
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
    console: typing.Any = None

    def __post_init__(self):
        if not RICH_INSTALLED:
            raise StlogError("Rich is not installed and RichStreamOutput is specified")
        if self.formatter is None:
            self.formatter = RichHumanFormatter()
        if self.console is None:
            self.console = Console(
                file=self.stream,
                force_terminal=True if self.force_terminal else None,
                highlight=False,
            )
        self.set_handler(CustomRichHandler(console=self.console))


def make_stream_or_rich_stream_output(
    stream: typing.TextIO = sys.stderr,
    use_rich: bool | None = DEFAULT_USE_RICH,
    **kwargs,
) -> StreamOutput:
    """Create automatically a `stlog.output.RichStreamOutput` or a (classic)`stlog.output.StreamOutput`.

    To get a `stlog.output.RichStreamOutput`, following conditions must be true:

    - `rich` library must be installed and available in python path
    - `use_rich` parameter must be `True` (forced mode) or `None` (automatic mode)
    - (if `use_rich` is `None`): the selected `stream` must "output" in a real terminal (not in a shell filter
    or in a file through redirection...)

    WARNING: if `use_rich` is set to True and if `rich` library is installed, the usage of `rich` library
    is forced **even if the `rich` library thinks that the output is not "compatible"

    NOTE: the default value of the `use_rich` parameter is `None` (automatic) but it can be forced by
    the `STLOG_USE_RICH` env variable.

    Attributes:
        stream: the stream to use (`typing.TextIO`), default to `sys.stderr`.
        use_rich: if None, use [rich output](https://github.com/Textualize/rich/blob/master/README.md) if possible
        (rich installed and supported tty), if True/False force the usage (or not).

    """
    for key in ("formatter", "force_terminal"):
        if key in kwargs:
            raise StlogError(f"you can't use {key} in kwargs for this function")
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
        return RichStreamOutput(
            stream=stream, force_terminal=True, formatter=RichHumanFormatter(), **kwargs
        )
    else:
        return StreamOutput(stream=stream, **kwargs)
