from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import typing
from dataclasses import dataclass, field

from stlog.base import (
    GLOBAL_LOGGING_CONFIG,
    StlogError,
    check_env_false,
)
from stlog.filter import ContextReinjectFilter
from stlog.formatter import (
    Formatter,
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
        reinject_context_in_standard_logging: if True, reinject the LogContext
            in log record emitted with python standard loggers
            (note: override `stlog.setup` default value for this output).
        read_extra_kwargs_from_standard_logging: if try to reinject the extra kwargs from standard logging
            (note: override `stlog.setup` default value for this output).

    """

    _handler: logging.Handler = field(init=False, default_factory=logging.NullHandler)
    formatter: logging.Formatter | None = None
    level: int | str | None = None
    filters: typing.Iterable[
        typing.Callable[[logging.LogRecord], bool] | logging.Filter
    ] = field(default_factory=list)
    reinject_context_in_standard_logging: bool | None = None
    read_extra_kwargs_from_standard_logging: bool | None = None

    @property
    def _reinject_context_in_standard_logging(self) -> bool:
        # lazy evaluation because Output are built before setup() call
        if self.reinject_context_in_standard_logging is not None:
            return self.reinject_context_in_standard_logging
        if GLOBAL_LOGGING_CONFIG.reinject_context_in_standard_logging is not None:
            return GLOBAL_LOGGING_CONFIG.reinject_context_in_standard_logging
        return check_env_false("STLOG_REINJECT_CONTEXT_IN_STANDARD_LOGGING", True)

    @property
    def _read_extra_kwargs_from_standard_logging(self) -> bool:
        # lazy evaluation because Output are built before setup() call
        if self.read_extra_kwargs_from_standard_logging is not None:
            return self.read_extra_kwargs_from_standard_logging
        if GLOBAL_LOGGING_CONFIG.read_extra_kwargs_from_standard_logging is not None:
            return GLOBAL_LOGGING_CONFIG.read_extra_kwargs_from_standard_logging
        return check_env_false("STLOG_READ_EXTRA_KWARGS_FROM_STANDARD_LOGGING", True)

    def set_handler(
        self,
        handler: logging.Handler,
    ):
        """Configure the Python logging Handler to use."""
        self._handler = handler
        self._handler.setFormatter(self.get_formatter_or_raise())
        if self.level is not None:
            self._handler.setLevel(self.level)
        if self._reinject_context_in_standard_logging:
            self._handler.addFilter(
                ContextReinjectFilter(
                    read_extra_kwargs_from_standard_logging=self._read_extra_kwargs_from_standard_logging
                )
            )
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
    force_terminal: bool = False
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
    rich_formatter: Formatter | None = None,
    not_rich_formatter: Formatter | None = None,
    **kwargs,
) -> StreamOutput:
    """Create automatically a `stlog.output.RichStreamOutput` or a (classic)`stlog.output.StreamOutput`.

    To get a `stlog.output.RichStreamOutput`, following conditions must be true:

    - `rich` library must be installed and available in python path
    - `use_rich` parameter must be `True` (forced mode) or `None` (automatic mode)
    - (if `use_rich` is `None`): the selected `stream` must "output" in a real terminal (not in a shell filter
    or in a file through redirection...)

    NOTE: the default value of the `use_rich` parameter is `None` (automatic) but it can be forced by
    the `STLOG_USE_RICH` env variable.

    Attributes:
        stream: the stream to use (`typing.TextIO`), default to `sys.stderr`.
        use_rich: if None, use [rich output](https://github.com/Textualize/rich/blob/master/README.md) if possible
            (rich installed and supported tty), if True/False force the usage (or not).
        rich_formatter: Formatter to use if rich is available/selected (None => default RichHumanFormatter instance).
        not_rich_formatter: Formatter to use if rich is not available/selected (None => default HumanFormatter instance).

    """
    if "formatter" in kwargs:
        raise StlogError(
            "you can't use formatter in kwargs for this function (buy you can use rich_formatter/not_rich_formatter instead)"
        )
    _use_rich: bool = False
    if use_rich is not None:
        # manual mode
        _use_rich = use_rich
    # automatic mode
    elif RICH_INSTALLED:
        c = Console(file=stream)
        _use_rich = c.is_terminal
    if _use_rich:
        return RichStreamOutput(
            stream=stream,
            formatter=rich_formatter or RichHumanFormatter(),
            **kwargs,
        )
    else:
        return StreamOutput(
            stream=stream,
            formatter=not_rich_formatter or HumanFormatter(),
            **kwargs,
        )


@dataclass
class FileOutput(Output):
    """Represent an output to a file.

    Attributes:
        filename: the filename to use.
        mode: the mode to use, default to "a".
        encoding: the encoding to use, default to None.
        delay: if True, the file is not opened until the first call to emit().
        errors: the errors to use, default to None (python >= 3.9 only)

    """

    filename: str = ""
    mode: str = "a"
    encoding: str | None = None
    delay: bool = False
    errors: str | None = None

    def __post_init__(self):
        if not self.filename:
            raise StlogError("filename is not set")
        if self.formatter is None:
            self.formatter = HumanFormatter()
        kwargs = {
            "mode": self.mode,
            "encoding": self.encoding,
            "delay": self.delay,
        }
        if sys.version_info >= (3, 9):
            kwargs["errors"] = self.errors
        self.set_handler(
            logging.FileHandler(self.filename, **kwargs),  # type: ignore
        )


@dataclass
class RotatingFileOutput(FileOutput):
    """Represent an output to a rotating file.

    Attributes:
        filename: the filename to use.
        mode: the mode to use, default to "a".
        max_bytes: the maximum number of bytes to use, default to 0.
        backup_count: the number of backup files to use, default to 0.
        encoding: the encoding to use, default to None.
        delay: if True, the file is not opened until the first call to emit().
        errors: the errors to use, default to None.

    """

    max_bytes: int = 0
    backup_count: int = 0

    def __post_init__(self):
        if not self.filename:
            raise StlogError("filename is not set")
        if self.formatter is None:
            self.formatter = HumanFormatter()
        kwargs = {
            "mode": self.mode,
            "encoding": self.encoding,
            "delay": self.delay,
            "backupCount": self.backup_count,
            "maxBytes": self.max_bytes,
        }
        if sys.version_info >= (3, 9):
            kwargs["errors"] = self.errors
        self.set_handler(
            logging.handlers.RotatingFileHandler(
                self.filename,
                **kwargs,  # type: ignore
            ),
        )
