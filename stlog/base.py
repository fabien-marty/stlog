from __future__ import annotations

import inspect
import json
import numbers
import os
import re
import types
from dataclasses import dataclass, field
from typing import Any, Callable, Match

STLOG_EXTRA_KEY = "_stlog_extra"
RICH_AVAILABLE = False
try:
    from rich.traceback import Traceback

    RICH_AVAILABLE = True
except ImportError:
    pass


TRUE_VALUES = ("1", "true", "yes")


class StLogError(Exception):
    pass


@dataclass
class GlobalLoggingConfig:
    program_name: str = field(
        default_factory=lambda: os.path.basename(inspect.stack()[-1][1])
    )
    _unit_tests_mode: bool = (
        os.environ.get("STLOG_UNIT_TESTS_MODE", "0").lower() in TRUE_VALUES
    )


GLOBAL_LOGGING_CONFIG = GlobalLoggingConfig()

# skip natural LogRecord attributes
# http://docs.python.org/library/logging.html#logrecord-attributes
# Stolen from https://github.com/madzak/python-json-logger/blob/master/src/pythonjsonlogger/jsonlogger.py
RESERVED_ATTRS: tuple[str, ...] = (
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "extra",  # specific to stlog
    "rich_escaped_message",  # specific to stlog
    "rich_escaped_extras",  # specific to stlog
    "rich_level_style",  # specific to stlog
)


def check_json_types_or_raise(to_check: Any) -> None:
    if to_check is None:
        return
    if not isinstance(to_check, (dict, list, bool, str, int, float, bool)):
        raise StLogError(
            "to_check should be a dict/list/bool/str/int/float/bool/None, found %s"
            % type(to_check)
        )
    if isinstance(to_check, list):
        for item in to_check:
            check_json_types_or_raise(item)
    elif isinstance(to_check, dict):
        for key, value in to_check.items():
            if not isinstance(key, str):
                raise StLogError("dict keys should be str, found %s" % type(key))
            check_json_types_or_raise(value)


# Adapted from https://github.com/jteppinette/python-logfmter/blob/main/logfmter/formatter.py
def logfmt_format_string(value: str) -> str:
    needs_dquote_escaping = '"' in value
    needs_newline_escaping = "\n" in value
    needs_quoting = " " in value or "=" in value
    if needs_dquote_escaping:
        value = value.replace('"', '\\"')
    if needs_newline_escaping:
        value = value.replace("\n", "\\n")
    if needs_quoting:
        value = f'"{value}"'
    return value if value else '""'


# Adapted from https://github.com/jteppinette/python-logfmter/blob/main/logfmter/formatter.py
def logfmt_format_value(value: Any) -> str:
    if value is None:
        return ""
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, numbers.Number):
        return str(value)
    return logfmt_format_string(str(value))


# Adapted from https://github.com/jteppinette/python-logfmter/blob/main/logfmter/formatter.py
def logfmt_format(kvs: dict[str, Any], ignore_compound_types: bool = True) -> str:
    return " ".join(
        [
            f"{key}={logfmt_format_value(value)}"
            for key, value in kvs.items()
            if not ignore_compound_types or (not isinstance(value, (dict, list, set)))
        ]
    )


# Adapted from https://github.com/jteppinette/python-logfmter/blob/main/logfmter/formatter.py
def rich_logfmt_format(kvs: dict[str, Any], ignore_compound_types: bool = True) -> str:
    return " ".join(
        [
            f"[repr.attrib_name]{key}[/repr.attrib_name][repr.attrib_equal]=[/repr.attrib_equal][repr.attrib_value]{logfmt_format_value(value)}[/repr.attrib_value]"
            for key, value in kvs.items()
            if not ignore_compound_types or (not isinstance(value, (dict, list, set)))
        ]
    )


def _get_env_json_context() -> dict[str, Any]:
    env_key = "STLOG_ENV_JSON_CONTEXT"
    env_context = os.environ.get(env_key, None)
    if env_context is not None:
        try:
            return json.loads(env_context)
        except Exception:
            print(
                f"WARNING: can't load {env_key} env var value as valid JSON => ignoring"
            )
    return {}


def _get_env_context() -> dict[str, Any]:
    prefix = "STLOG_ENV_CONTEXT_"
    res: dict[str, Any] = {}
    for env_key in os.environ.keys():
        if not env_key.startswith(prefix):
            continue
        key = env_key[len(prefix) :].lower()
        if not key:
            continue
        res[key] = os.environ[env_key]
    return res


def get_env_context() -> dict[str, Any]:
    if check_env_true("STLOG_IGNORE_ENV_CONTEXT", False):
        return {}
    env_context = {**_get_env_context(), **_get_env_json_context()}
    for key in env_context.keys():
        if key in RESERVED_ATTRS:
            raise StLogError("key: %s is not allowed (reserved key)", key)
        if not isinstance(key, str):
            raise StLogError("key: %s must be str", key)
        if not key.isidentifier():
            raise StLogError(
                "key: %s not allowed (must be a valid python identifier)", key
            )
    return env_context


def check_true(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.lower() in TRUE_VALUES


def check_env_true(env_var: str, default: bool = False) -> bool:
    return check_true(os.environ.get("env_var", None), default)


def rich_dump_exception_on_console(
    console: Any,
    exc_type: type[BaseException],
    value: BaseException,
    tb: types.TracebackType | None,
) -> None:
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


_ReStringMatch = Match[str]  # regex match object
_ReSubCallable = Callable[[_ReStringMatch], str]  # Callable invoked by re.sub
_EscapeSubMethod = Callable[[_ReSubCallable, str], str]  # Sub method of a compiled re


# Stolen from https://github.com/Textualize/rich/blob/master/rich/markup.py
def rich_markup_escape(
    markup: str,
    _escape: _EscapeSubMethod = re.compile(r"(\\*)(\[[a-z#/@][^[]*?])").sub,
) -> str:
    def escape_backslashes(match: Match[str]) -> str:
        """Called by re.sub replace matches."""
        backslashes, text = match.groups()
        return f"{backslashes}{backslashes}\\{text}"

    markup = _escape(escape_backslashes, markup)
    return markup
