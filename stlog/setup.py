from __future__ import annotations

import logging
import sys
import traceback
import types as _ptypes
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

DEFAULT_OUTPUTS = [Stream(stream=sys.stderr)]


def logging_excepthook(
    program_name: str | None,
    exc_type: type[BaseException],
    value: BaseException,
    tb: _ptypes.TracebackType,
) -> None:
    try:
        program_logger = getLogger(program_name)
        program_logger.critical(
            "".join(traceback.format_exception(exc_type, value, tb))
        )
        dump_exception_on_console(exc_type, value, tb)
    except Exception:
        print(
            "ERROR: Exception during exception handling => let's dump this on standard output"
        )
        print(traceback.format_exc(), file=sys.stderr)


def dump_exception_on_console(
    exc_type: type[BaseException],
    value: BaseException,
    tb: _ptypes.TracebackType,
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
    level: int = logging.WARNING,
    outputs: typing.Iterable[Output] | None = None,
    program_name: str | None = None,
    capture_warnings: bool = True,
    logging_excepthook=logging_excepthook,
    extra_levels: typing.Iterable[tuple[str, str | int]] = [],
    reinject_context_in_standard_logging: bool = True,
) -> None:
    """Set up Python logging.

    This sets up basic handlers for Python logging.

    :param level: Root log level.
    :param outputs: Iterable of outputs to log to.
    :param program_name: The name of the program. Auto-detected if not set.
    :param capture_warnings: Capture warnings from the `warnings` module.
    """
    if outputs is None:
        outputs = DEFAULT_OUTPUTS
    root_logger = logging.getLogger(None)
    GLOBAL_LOGGING_CONFIG.reinject_context_in_standard_logging = (
        reinject_context_in_standard_logging
    )
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
        if isinstance(lvel, str):
            lvel = lvel.upper()
        logging.getLogger(lgger).setLevel(lvel)
