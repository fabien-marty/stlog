from __future__ import annotations

import fnmatch
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Sequence

from stlog.base import STLOG_EXTRA_KEY

DEFAULT_STLOG_HUMAN_FORMAT = (
    "%(asctime)s %(slevel_name)-10.10s %(name)s#%(process)d: %(message)s %(extras)s"
)
DEFAULT_STLOG_RICH_FORMAT = "%(name)s#%(process)d: %(message)s %(extras)s"
DEFAULT_STLOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _truncate_str(str_value: str, limit: int = 0) -> str:
    if limit <= 0:
        return str_value
    if len(str_value) > limit:
        return str_value[0 : (limit - 3)] + "..."
    return str_value


def _truncate_serialize(value: Any, limit: int = 0) -> str:
    try:
        serialized = str(value)
    except Exception:
        serialized = "[can't serialize]"
    return _truncate_str(serialized, limit)


@dataclass
class Formatter(logging.Formatter):
    """Abstract base class for `stlog` formatters.

    Attributes:
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

    fmt: str | None = DEFAULT_STLOG_HUMAN_FORMAT
    datefmt: str | None = DEFAULT_STLOG_DATE_FORMAT
    style: Literal["%", "{", "$"] = "%"
    validate: bool = True
    include_extras_keys_fnmatchs: Sequence[str] = ("*",)
    exclude_extras_keys_fnmatchs: Sequence[str] = ("_*",)
    extra_key_rename_fn: Callable[[str], str | None] | None = None
    extra_key_max_length: int = 32
    converter: Callable[[float | None], time.struct_time] = time.gmtime

    def __post_init__(self):
        super().__init__(  # explicit call because logging.Formatter is not a dataclass
            fmt=self.fmt, datefmt=self.datefmt, validate=self.validate, style=self.style
        )
        self.include_extra_keys_patterns: list[re.Pattern] = [
            re.compile(fnmatch.translate(x)) for x in self.include_extras_keys_fnmatchs
        ]
        self.exclude_extra_keys_patterns: list[re.Pattern] = [
            re.compile(fnmatch.translate(x)) for x in self.exclude_extras_keys_fnmatchs
        ]

    def _make_extra_key_name(self, extra_key: str) -> str | None:
        new_extra_key: str | None = extra_key
        if self.extra_key_rename_fn is not None:
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
        return _truncate_str(new_extra_key, self.extra_key_max_length)


# Adapted from https://github.com/Mergifyio/daiquiri/blob/main/daiquiri/formatter.py
@dataclass
class HumanFormatter(Formatter):
    """Formatter for a "human" output.

    Extra keywords are merged into a `%(extras)s` placeholder.

    If you use this placeholder on your `fmt`, any keywords
    passed to a logging call will be formatted into a "extras" string and
    included in a logging message.

    Example::

        logger.info("my message", foo="bar", foo2=123)

    will cause an "extras" string of::

        [foo: bar] [foo2: 123]

    Note: a `%(slevel_name)s` placeholder is also added containing the uppercase
        level name under brackets, example: `[CRITICAL]`, `[WARNING]`, ...

    Attributes:
        extras_template: the template to format a key/value.
        extras_separator: the separator between multiple key/values.
        extras_prefix: the prefix before key/value parts.
        extras_suffix: the suffix after key/values parts.
        extra_value_max_serialized_length: maximum size of extra values to be included in `%(extras)s` placeholder
            (after this limit, the value will be truncated and ... will be added at the end, 0 means "no limit").

    """

    extras_template: str = "[{0}: {1}]"
    extras_separator: str = " "
    extras_prefix: str = " "
    extras_suffix: str = ""
    extra_value_max_serialized_length: int = 40

    def _add_extras(self, record: logging.LogRecord) -> None:
        record.slevel_name = f"[{record.levelname}]"
        if not hasattr(record, STLOG_EXTRA_KEY):
            record.extras = ""
            return
        tmp = []
        for k in getattr(record, STLOG_EXTRA_KEY):
            key = self._make_extra_key_name(k)
            if not key:
                continue
            serialized = _truncate_serialize(
                getattr(record, k), self.extra_value_max_serialized_length
            )
            if serialized is None:
                continue
            tmp.append(self.extras_template.format(key, serialized))
        extras = self.extras_separator.join(tmp)
        if extras != "":
            extras = self.extras_prefix + extras + self.extras_suffix
        record.extras = extras

    def _remove_extras(self, record: logging.LogRecord) -> None:
        delattr(record, "extras")
        delattr(record, "slevel_name")

    def format(self, record: logging.LogRecord) -> str:
        self._add_extras(record)
        s = super().format(record)
        self._remove_extras(record)
        return s


def json_formatter_default_extra_key_rename_fn(key: str) -> str | None:
    if key.startswith("_"):
        return key[1:]
    return key


@dataclass
class JsonFormatter(Formatter):
    """Formatter for a JSON / parsing friendly output."""

    extra_key_max_length: int = 0
    exclude_extras_keys_fnmatchs: Sequence[str] = field(default_factory=list)
    extra_key_rename_fn: Callable[
        [str], str | None
    ] | None = json_formatter_default_extra_key_rename_fn

    def json_serialize(self, message_dict: dict[str, Any]) -> str:
        return json.dumps(message_dict, default=lambda x: "[can't serialize]")

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
            key = self._make_extra_key_name(k)
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
