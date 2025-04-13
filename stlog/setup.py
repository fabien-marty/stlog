from __future__ import annotations

import logging
import os
import sys
import traceback
import types
import typing
import warnings

from stlog.adapter import getLogger
from stlog.base import GLOBAL_LOGGING_CONFIG, check_env_false
from stlog.formatter import DEFAULT_STLOG_GCP_JSON_FORMAT, JsonFormatter
from stlog.output import Output, StreamOutput, make_stream_or_rich_stream_output

DEFAULT_LEVEL: str = os.environ.get("STLOG_LEVEL", "INFO")
DEFAULT_CAPTURE_WARNINGS: bool = check_env_false("STLOG_CAPTURE_WARNINGS", True)
DEFAULT_PROGRAM_NAME: str | None = os.environ.get("STLOG_PROGRAM_NAME", None)
DEFAULT_DESTINATION: str = os.environ.get("STLOG_DESTINATION", "stderr").lower()
DEFAULT_OUTPUT: str = os.environ.get("STLOG_OUTPUT", "console").lower()


def _make_default_stream() -> typing.TextIO:
    if DEFAULT_DESTINATION == "stderr":
        return sys.stderr
    elif DEFAULT_DESTINATION == "stdout":
        return sys.stdout
    raise Exception(
        f"bad value:{DEFAULT_DESTINATION} for STLOG_DESTINATION env var => must be 'stderr' or 'stdout'"
    )


def _make_default_outputs() -> list[Output]:
    if DEFAULT_OUTPUT == "console":
        return [make_stream_or_rich_stream_output(stream=_make_default_stream())]
    elif DEFAULT_OUTPUT == "json":
        return [StreamOutput(stream=_make_default_stream(), formatter=JsonFormatter())]
    elif DEFAULT_OUTPUT == "json-human":
        return [
            StreamOutput(
                stream=_make_default_stream(), formatter=JsonFormatter(indent=4)
            )
        ]
    elif DEFAULT_OUTPUT == "json-gcp":
        return [
            StreamOutput(
                stream=_make_default_stream(),
                formatter=JsonFormatter(fmt=DEFAULT_STLOG_GCP_JSON_FORMAT),
            )
        ]
    else:
        raise Exception(
            f"bad value:{DEFAULT_OUTPUT} for STLOG_OUTPUT env var => must be 'console', 'json', 'json-human' or 'json-gcp'"
        )


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
        program_logger.error(
            "Exception catched in excepthook", exc_info=(exc_type, value, tb)
        )
    except Exception:
        print(
            "ERROR: Exception during exception handling => let's dump this on standard output"
        )
        print(traceback.format_exc(), file=sys.stderr)


def setup(  # noqa: PLR0913
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
    reinject_context_in_standard_logging: bool | None = None,
    read_extra_kwargs_from_standard_logging: bool | None = None,
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
        extra_levels: dict "logger name => log level" for quick override of
            the root log level (for some loggers).
        reinject_context_in_standard_logging: if True, reinject the LogContext
            in log record emitted with python standard loggers (note: can be overriden per `stlog.output.Output`,
            default to `STLOG_REINJECT_CONTEXT_IN_STANDARD_LOGGING` env var or True if not set).
        read_extra_kwargs_from_standard_logging: if try to reinject the extra kwargs from standard logging
            (note: can be overriden per `stlog.output.Output`, default to `STLOG_READ_EXTRA_KWARGS_FROM_STANDARD_LOGGING` env var
            or False if not set).

    """
    GLOBAL_LOGGING_CONFIG.reinject_context_in_standard_logging = (
        reinject_context_in_standard_logging
    )
    GLOBAL_LOGGING_CONFIG.read_extra_kwargs_from_standard_logging = (
        read_extra_kwargs_from_standard_logging
    )
    if program_name is not None:
        GLOBAL_LOGGING_CONFIG.program_name = program_name

    if GLOBAL_LOGGING_CONFIG._unit_tests_mode:
        # remove all configured loggers
        for key in list(logging.Logger.manager.loggerDict.keys()):
            logging.Logger.manager.loggerDict.pop(key)

    root_logger = logging.getLogger(None)
    # Remove all handlers
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Add configured handlers
    if outputs is None:
        outputs = _make_default_outputs()
    for out in outputs:
        root_logger.addHandler(out.get_handler())

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

    GLOBAL_LOGGING_CONFIG.setup = True


ROOT_LOGGER = getLogger("root")


def log(level: int, msg, *args, **kwargs):
    """Log a message with the given integer severity level' on the root logger.

    `setup()` is automatically called with default arguments if not already done before.
    """
    if not GLOBAL_LOGGING_CONFIG.setup:
        setup()
    ROOT_LOGGER.log(level, msg, *args, **kwargs)


def debug(msg, *args, **kwargs):
    """Log a message with severity 'DEBUG' on the root logger.

    `setup()` is automatically called with default arguments if not already done before.
    """
    log(logging.DEBUG, msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """Log a message with severity 'INFO' on the root logger.

    `setup()` is automatically called with default arguments if not already done before.
    """
    log(logging.INFO, msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """Log a message with severity 'WARNING' on the root logger.

    `setup()` is automatically called with default arguments if not already done before.
    """
    log(logging.WARNING, msg, *args, **kwargs)


def warn(msg, *args, **kwargs):
    if (
        not GLOBAL_LOGGING_CONFIG.setup
    ):  # we do this here to be able to capture the next warning
        setup()
    warnings.warn(
        "The 'warn' function is deprecated, use 'warning' instead",
        DeprecationWarning,
        2,
    )
    warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """Log a message with severity 'ERROR' on the root logger.

    `setup()` is automatically called with default arguments if not already done before.
    """
    log(logging.ERROR, msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """Log a message with severity 'CRITICAL' on the root logger.

    `setup()` is automatically called with default arguments if not already done before.
    """
    log(logging.CRITICAL, msg, *args, **kwargs)


fatal = critical


def exception(msg, *args, exc_info=True, **kwargs):
    """Log a message with severity 'ERROR' on the root logger with exception information.

    `setup()` is automatically called with default arguments if not already done before.
    """
    error(msg, *args, exc_info=exc_info, **kwargs)
