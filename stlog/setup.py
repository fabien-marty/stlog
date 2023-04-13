from __future__ import annotations

import logging
import os
import sys
import traceback
import types
import typing

from stlog.adapter import getLogger
from stlog.base import GLOBAL_LOGGING_CONFIG
from stlog.handler import ContextReinjectHandlerWrapper
from stlog.output import Output, Stream

RICH_AVAILABLE = True
try:
    pass
except ImportError:
    RICH_AVAILABLE = False

DEFAULT_OUTPUTS: list[Output] = [Stream(stream=sys.stderr)]
DEFAULT_LEVEL: str = os.environ.get("STLOG_LEVEL", "INFO")
DEFAULT_PROGRAM_NAME: str | None = os.environ.get("STLOG_PROGRAM_NAME", None)


def _logging_excepthook(
    exc_type: type[BaseException],
    value: BaseException,
    tb: types.TracebackType | None,
) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, value, tb)
        return
    try:
        program_logger = getLogger(GLOBAL_LOGGING_CONFIG.program_name)
        program_logger.critical(
            "Exception catched in excepthook", exc_info=(exc_type, value, tb)
        )
        _dump_exception_on_console(exc_type, value, tb)
    except Exception:
        print(
            "ERROR: Exception during exception handling => let's dump this on standard output"
        )
        print(traceback.format_exc(), file=sys.stderr)


def _dump_exception_on_console(
    exc_type: type[BaseException],
    value: BaseException,
    tb: types.TracebackType | None,
) -> None:
    if RICH_AVAILABLE:
        from rich.console import Console
        from rich.traceback import Traceback

        console = Console(file=sys.stderr)
        console.print(
            Traceback.from_exception(
                exc_type,
                value,
                tb,
                width=100,
                extra_lines=3,
                theme=None,
                word_wrap=False,
                show_locals=True,
                locals_max_length=10,
                locals_max_string=80,
                locals_hide_dunder=True,
                locals_hide_sunder=False,
                indent_guides=True,
                suppress=(),
                max_frames=100,
            )
        )
    else:
        print("".join(traceback.format_exception(exc_type, value, tb)), file=sys.stderr)


def setup(
    *,
    level: str | int = DEFAULT_LEVEL,
    outputs: typing.Iterable[Output] = DEFAULT_OUTPUTS,
    program_name: str | None = DEFAULT_PROGRAM_NAME,
    capture_warnings: bool = True,
    logging_excepthook: typing.Callable[
        [type[BaseException], BaseException, types.TracebackType | None],
        typing.Any,
    ]
    | None = _logging_excepthook,
    extra_levels: typing.Iterable[tuple[str, str | int]] = [],
    reinject_context_in_standard_logging: bool = True,
) -> None:
    """Set up the Python logging with stlog (globally).

    This removes all existing handlers and
    sets up handlers/formatters/... for Python logging.

    Args:
        level: the root log level as int or as a string representation (in uppercase)
            (see https://docs.python.org/3/library/logging.html#levels), the default
            value is read in STLOG_LEVEL env var or set to INFO (if not set).
        outputs: iterable of Output to log to.
        program_name: the name of the program, the default value is read in STLOG_PROGRAM_NAME
            env var or auto-detected if not set.
        capture_warnings: capture warnings from the `warnings` module.
        logging_excepthook: if not None, override sys.excepthook with the given callable
            See https://docs.python.org/3/library/sys.html#sys.excepthook for details.
        extra_levels: iterable of tuples (logger name, log level) for quick override of
            the root log level.
        reinject_context_in_standard_logging: if True, reinject the ExecutionLogContext
            in log record emitted with python standard loggers.
    """
    root_logger = logging.getLogger(None)
    GLOBAL_LOGGING_CONFIG.reinject_context_in_standard_logging = (
        reinject_context_in_standard_logging
    )
    if program_name is not None:
        GLOBAL_LOGGING_CONFIG.program_name = program_name

    # Remove all handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Add configured handlers
    for out in outputs:
        root_logger.addHandler(ContextReinjectHandlerWrapper(out.get_handler()))  # type: ignore

    root_logger.setLevel(level)

    if logging_excepthook:
        sys.excepthook = logging_excepthook

    if capture_warnings:
        logging.captureWarnings(True)

    for lgger, lvel in extra_levels:
        logging.getLogger(lgger).setLevel(lvel)
