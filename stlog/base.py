from __future__ import annotations

import inspect
import json
import numbers
import os
from dataclasses import dataclass, field
from typing import Any

STLOG_EXTRA_KEY = "_stlog_extra"


class StLogError(Exception):
    pass


@dataclass
class GlobalLoggingConfig:
    program_name: str = field(
        default_factory=lambda: os.path.basename(inspect.stack()[-1][1])
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


def _get_env_json_context() -> dict[str, Any]:
    """FIXME"""
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
    if os.environ.get("STLOG_IGNORE_ENV_CONTEXT", "0").lower().strip() in (
        "1",
        "true",
        "yes",
    ):
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
