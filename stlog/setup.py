from __future__ import annotations

import logging
import os
import sys
import traceback
import types
import typing

from stlog.adapter import getLogger
from stlog.base import GLOBAL_LOGGING_CONFIG, check_env_true
from stlog.handler import ContextReinjectHandlerWrapper
from stlog.output import Output, make_stream_or_rich_stream_output

DEFAULT_LEVEL: str = os.environ.get("STLOG_LEVEL", "INFO")
DEFAULT_CAPTURE_WARNINGS: bool = check_env_true("STLOG_CAPTURE_WARNINGS", True)
DEFAULT_REINJECT_CONTEXT_IN_STANDARD_LOGGING: bool = check_env_true(
    "STLOG_REINJECT_CONTEXT_IN_STANDARD_LOGGING", True
)
DEFAULT_PROGRAM_NAME: str | None = os.environ.get("STLOG_PROGRAM_NAME", None)


def _make_default_outputs() -> list[Output]:
    return [make_stream_or_rich_stream_output(stream=sys.stderr)]


def _logging_excepthook(
    exc_type: type[BaseException],
    value: BaseException,
    tb: types.TracebackType | None = None,
) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, value, tb)
        return
    try:
        program_logger = getLogger(GLOBAL_LOGGING_CONFIG.program_name)
        program_logger.critical(
            "Exception catched in excepthook", exc_info=(exc_type, value, tb)
        )
    except Exception:
        print(
            "ERROR: Exception during exception handling => let's dump this on standard output"
        )
        print(traceback.format_exc(), file=sys.stderr)


def setup(
    *,
    level: str | int = DEFAULT_LEVEL,
    outputs: typing.Iterable[Output] | None = None,
    program_name: str | None = DEFAULT_PROGRAM_NAME,
    capture_warnings: bool = DEFAULT_CAPTURE_WARNINGS,
    logging_excepthook: typing.Callable[
        [type[BaseException], BaseException, types.TracebackType | None],
        typing.Any,
    ]
    | None = _logging_excepthook,
    extra_levels: typing.Mapping[str, str | int] = {},
    reinject_context_in_standard_logging: bool = DEFAULT_REINJECT_CONTEXT_IN_STANDARD_LOGGING,
    read_extra_kwarg_from_standard_logging: bool = False,
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
        read_extra_kwarg_from_standard_logging: if try to reinject the extra kwargs from standard logging.
    """
    root_logger = logging.getLogger(None)
    if program_name is not None:
        GLOBAL_LOGGING_CONFIG.program_name = program_name

    if GLOBAL_LOGGING_CONFIG._unit_tests_mode:
        # remove all configured loggers
        for key in list(logging.Logger.manager.loggerDict.keys()):
            logging.Logger.manager.loggerDict.pop(key)

    # Remove all handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Add configured handlers
    if outputs is None:
        outputs = _make_default_outputs()
    for out in outputs:
        if reinject_context_in_standard_logging:
            handler = ContextReinjectHandlerWrapper(
                wrapped=out.get_handler(),
                read_extra_kwarg_from_standard_logging=read_extra_kwarg_from_standard_logging,
            )
        else:
            handler = out.get_handler()
        root_logger.addHandler(handler)

    root_logger.setLevel(level)

    if logging_excepthook:
        sys.excepthook = logging_excepthook

    if capture_warnings:
        if GLOBAL_LOGGING_CONFIG._unit_tests_mode:
            # to avoid the capture by pytest
            logging._warnings_showwarning = None  # type: ignore
        logging.captureWarnings(True)

    for lgger, lvel in extra_levels.items():
        logging.getLogger(lgger).setLevel(lvel)
