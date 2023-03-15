from __future__ import annotations

import fnmatch
import json
import logging
import re
import time
from typing import Any, Callable, Literal, Sequence

from stlog.base import STLOG_EXTRA_KEY

DEFAULT_STLOG_HUMAN_FORMAT = (
    "%(asctime)s %(slevel_name)-10.10s %(name)s#%(process)d: %(message)s %(extras)s"
)
DEFAULT_STLOG_RICH_FORMAT = "%(name)s#%(process)d: %(message)s %(extras)s"
DEFAULT_STLOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def truncate_str(str_value: str, limit: int = 0) -> str:
    if limit <= 0:
        return str_value
    if len(str_value) > limit:
        return str_value[0 : (limit - 3)] + "..."
    return str_value


def truncate_serialize(value: Any, limit: int = 0) -> str:
    try:
        serialized = str(value)
    except Exception:
        serialized = "[can't serialize]"
    return truncate_str(serialized, limit)


class _Formatter(logging.Formatter):
    """
    Args:
        fmt: the default format for the formatter.
        datefmt: the format to use for `%(asctime)s` placeholder.
        include_extras_keys_fnmatchs: fnmatch patterns list for including keys in `%(extras)s` placeholder.
        exclude_extras_keys_fnmatchs: fnmatch patterns list for excluding keys in `%(extras)s` placeholder.
        extra_key_rename_fn: FIXME
        extra_key_max_length: maximum size of extra keys to be included in `%(extras)s` placeholder
            (after this limit, the value will be truncated and ... will be added at the end, 0 means "no limit").
        converter: time converter function (use `time.gmtime` (default) for UTC date/times, use `time.time`
            for local date/times), if you change the default, please change also `datefmt` keyword.
    """

    def __init__(  # noqa: PLR0913
        self,
        fmt: str | None = DEFAULT_STLOG_HUMAN_FORMAT,
        datefmt: str | None = DEFAULT_STLOG_DATE_FORMAT,
        style: Literal["%", "{", "$"] = "%",
        validate: bool = True,
        include_extras_keys_fnmatchs: Sequence[str] = ("*",),
        exclude_extras_keys_fnmatchs: Sequence[str] = ("_*",),
        extra_key_rename_fn: Callable[[str], str | None] = lambda x: x,
        extra_key_max_length: int = 32,
        converter: Callable[[float | None], time.struct_time] = time.gmtime,
        **kwargs,
    ):
        super().__init__(
            fmt=fmt, datefmt=datefmt, style=style, validate=validate, **kwargs
        )
        self.include_extra_keys_patterns: list[re.Pattern] = [
            re.compile(fnmatch.translate(x)) for x in include_extras_keys_fnmatchs
        ]
        self.exclude_extra_keys_patterns: list[re.Pattern] = [
            re.compile(fnmatch.translate(x)) for x in exclude_extras_keys_fnmatchs
        ]
        self.converter: Callable[[float | None], time.struct_time] = converter
        self.extra_key_max_length = extra_key_max_length
        self.extra_key_rename_fn = extra_key_rename_fn

    def make_extra_key_name(self, extra_key: str) -> str | None:
        new_extra_key = (self.extra_key_rename_fn)(extra_key)
        if new_extra_key is None:
            return None
        for pattern in self.include_extra_keys_patterns:
            if re.match(pattern, new_extra_key):
                break
        else:
            # not found
            return None
        for pattern in self.exclude_extra_keys_patterns:
            if re.match(pattern, new_extra_key):
                return None
        return truncate_str(new_extra_key, self.extra_key_max_length)


# Adapted from https://github.com/Mergifyio/daiquiri/blob/main/daiquiri/formatter.py
class HumanFormatter(_Formatter):
    """Formatter for a "human" output.

    Extra keywords are merged into a `%(extras)s` placeholder.

    If you use this placeholder on your `fmt`, any keywords
    passed to a logging call will be formatted into a "extras" string and
    included in a logging message.

    Example:
        logger.info("my message", foo="bar", foo2=123)

    will cause an "extras" string of:
        [foo: bar] [foo2: 123]

    Note: a `%(slevel_name)s` placeholder is also added containing the uppercase
        level name under brackets, example: `[CRITICAL]`, `[WARNING]`, ...

    Args:
        extras_template: the template to format a key/value.
        extras_separator: the separator between multiple key/values.
        extras_prefix: the prefix before key/value parts.
        extras_suffix: the suffix after key/values parts.
        extra_value_max_serialized_length: maximum size of extra values to be included in `%(extras)s` placeholder
            (after this limit, the value will be truncated and ... will be added at the end, 0 means "no limit").
        converter: time converter function (use `time.gmtime` (default) for UTC date/times, use `time.time`
            for local date/times), if you change the default, please change also `datefmt` keyword.

    """

    def __init__(  # noqa: PLR0913
        self,
        extras_template: str = "[{0}: {1}]",
        extras_separator: str = " ",
        extras_prefix: str = " ",
        extras_suffix: str = "",
        extra_value_max_serialized_length: int = 40,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.extras_template = extras_template
        self.extras_separator = extras_separator
        self.extras_prefix = extras_prefix
        self.extras_suffix = extras_suffix
        self.extra_value_max_serialized_length = extra_value_max_serialized_length

    def add_extras(self, record: logging.LogRecord) -> None:
        record.slevel_name = f"[{record.levelname}]"
        if not hasattr(record, STLOG_EXTRA_KEY):
            record.extras = ""
            return
        tmp = []
        for k in getattr(record, STLOG_EXTRA_KEY):
            key = self.make_extra_key_name(k)
            if not key:
                continue
            serialized = truncate_serialize(
                getattr(record, k), self.extra_value_max_serialized_length
            )
            if serialized is None:
                continue
            tmp.append(self.extras_template.format(key, serialized))
        extras = self.extras_separator.join(tmp)
        if extras != "":
            extras = self.extras_prefix + extras + self.extras_suffix
        record.extras = extras

    def remove_extras(self, record: logging.LogRecord) -> None:
        delattr(record, "extras")
        delattr(record, "slevel_name")

    def format(self, record: logging.LogRecord) -> str:
        self.add_extras(record)
        s = super().format(record)
        self.remove_extras(record)
        return s


class JsonFormatter(_Formatter):
    """Formatter for a JSON / parsing friendly output."""

    def json_serialize(self, message_dict: dict[str, Any]) -> str:
        return json.dumps(message_dict, default=truncate_serialize)

    def format(self, record: logging.LogRecord) -> str:
        message_dict: dict[str, Any] = {
            "status": record.levelname.lower(),
            "logger": {"name": record.name},
            "source": {
                "path": record.pathname,
                "lineno": record.lineno,
                "module": record.module,
                "funcName": record.funcName,
            },
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, self.datefmt),
        }
        for k in ("process", "processName", "thread", "threadName"):
            if getattr(record, k, None):
                message_dict["source"][k] = getattr(record, k)
        for k in getattr(record, STLOG_EXTRA_KEY, set()):
            key = self.make_extra_key_name(k)
            if not key:
                continue
            message_dict[key] = getattr(record, k)
            message_dict["timestamp"] = self.formatTime(record, self.datefmt)
        if record.exc_info:
            message_dict["exc_info"] = self.formatException(record.exc_info)
        elif record.exc_text:
            message_dict["exc_info"] = record.exc_text
        if record.stack_info:
            message_dict["stack_info"] = self.formatStack(record.stack_info)
        return self.json_serialize(message_dict)
