from __future__ import annotations

import fnmatch
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from stlog.base import (
    GLOBAL_LOGGING_CONFIG,
    STLOG_EXTRA_KEY,
    check_env_true,
    logfmt_format,
    rich_logfmt_format,
    rich_markup_escape,
)

DEFAULT_STLOG_HUMAN_FORMAT = "{asctime} {name} [{levelname:^10s}] {message}{extras}"
DEFAULT_STLOG_RICH_HUMAN_FORMAT = ":arrow_forward: [log.time]{asctime}[/log.time] {name} [{rich_level_style}]{levelname:^8s}[/{rich_level_style}] [bold]{rich_escaped_message}[/bold]{extras}"
DEFAULT_STLOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
STLOG_DEFAULT_LOGFMT_IGNORE_COMPOUND_TYPES = check_env_true(
    "STLOG_LOGFMT_IGNORE_COMPOUND_TYPES", True
)


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


def _unit_tests_converter(val: float | None) -> time.struct_time:
    # always the same value
    return time.gmtime(1680101317)


@dataclass
class Formatter(logging.Formatter):
    """Abstract base class for `stlog` formatters.

    Attributes:
        fmt: the default format for the formatter.
        datefmt: the format to use for `{asctime}` placeholder.
        style: FIXME
        include_extras_keys_fnmatchs: fnmatch patterns list for including keys in `{extra}` placeholder.
        exclude_extras_keys_fnmatchs: fnmatch patterns list for excluding keys in `{extra}` placeholder.
        extra_key_rename_fn: callable which takes a key name and return a renamed key to use
            (or None to ignore the key/value).
        extra_key_max_length: maximum size of extra keys to be included in `{extra}` placeholder
            (after this limit, the value will be truncated and ... will be added at the end, 0 means "no limit").
        converter: time converter function (use `time.gmtime` (default) for UTC date/times, use `time.time`
            for local date/times), if you change the default, please change also `datefmt` keyword.

    """

    fmt: str | None = DEFAULT_STLOG_HUMAN_FORMAT
    datefmt: str | None = DEFAULT_STLOG_DATE_FORMAT
    style: str = "{"
    include_extras_keys_fnmatchs: Sequence[str] = ("*",)
    exclude_extras_keys_fnmatchs: Sequence[str] = ("_*",)
    extra_key_rename_fn: Callable[[str], str | None] | None = None
    extra_key_max_length: int = 32
    converter: Callable[[float | None], time.struct_time] = time.gmtime

    def __post_init__(self):
        super().__init__(  # explicit call because logging.Formatter is not a dataclass
            fmt=self.fmt, datefmt=self.datefmt, style=self.style  # type: ignore
        )
        self.include_extra_keys_patterns: list[re.Pattern] = [
            re.compile(fnmatch.translate(x)) for x in self.include_extras_keys_fnmatchs
        ]
        self.exclude_extra_keys_patterns: list[re.Pattern] = [
            re.compile(fnmatch.translate(x)) for x in self.exclude_extras_keys_fnmatchs
        ]
        if GLOBAL_LOGGING_CONFIG._unit_tests_mode:
            self.converter = _unit_tests_converter

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

    def format(self, record: logging.LogRecord) -> str:
        if GLOBAL_LOGGING_CONFIG._unit_tests_mode:
            # fix some fields in record to get always the same values
            record.filename = "filename.py"
            record.pathname = "/path/filename.py"
            record.thread = 12345
            record.process = 6789
            record.processName = "MainProcess"
            record.threadName = "MainThread"
        return super().format(record)


@dataclass
class KVFormatter(ABC):
    """Abstract base class to format extras key-values."""

    @abstractmethod
    def format(self, kvs: dict[str, Any]) -> str:
        pass


# Adapted from https://github.com/Mergifyio/daiquiri/blob/main/daiquiri/formatter.py
@dataclass
class TemplateKVFormatter(KVFormatter):
    """Class to format extra key-values as a string with templates.

    Extra keywords are merged into a `{extra}` placeholder.

    Example::

        {foo="bar", foo2=123}

    will be formatted as:

        [foo: bar] [foo2: 123]

    Attributes:
        extras_template: the template to format a key/value:
            `{0}` placeholder is the key, `{1}` is the value.
        extras_separator: the separator between multiple key/values.
        extras_prefix: the prefix before key/value parts.
        extras_suffix: the suffix after key/values parts.
        extra_value_max_serialized_length: maximum size of extra values to be included in `{extra}` placeholder
            (after this limit, the value will be truncated and ... will be added at the end, 0 means "no limit").

    """

    extras_template: str = "[{0}: {1}]"
    extras_separator: str = " "
    extras_prefix: str = " "
    extras_suffix: str = ""
    extra_value_max_serialized_length: int = 40

    def format(self, kvs: dict[str, Any]) -> str:
        res: str = ""
        tmp: list[str] = []
        for k, v in sorted(kvs.items(), key=lambda x: x[0]):
            serialized = _truncate_serialize(v, self.extra_value_max_serialized_length)
            if serialized is None:
                continue
            tmp.append(self.extras_template.format(k, serialized))
        res = self.extras_separator.join(tmp)
        if res != "":
            res = self.extras_prefix + res + self.extras_suffix
        return res


# Adapted from https://github.com/jteppinette/python-logfmter/blob/main/logfmter/formatter.py
@dataclass
class LogFmtKVFormatter(KVFormatter):
    ignore_compound_types: bool = STLOG_DEFAULT_LOGFMT_IGNORE_COMPOUND_TYPES
    extras_prefix: str = " {"
    extras_suffix: str = "}"

    def _format(self, kvs: dict[str, Any]) -> str:
        return logfmt_format(
            dict(sorted(kvs.items())), ignore_compound_types=self.ignore_compound_types
        )

    def format(self, kvs: dict[str, Any]) -> str:
        tmp = self._format(kvs)
        if not tmp:
            return ""
        return self.extras_prefix + tmp + self.extras_suffix


@dataclass
class RichLogFmtKVFormatter(LogFmtKVFormatter):
    extras_prefix: str = "\n    :arrow_right_hook: "
    extras_suffix: str = ""

    def _format(self, kvs: dict[str, Any]) -> str:
        return rich_logfmt_format(
            dict(sorted(kvs.items())), ignore_compound_types=self.ignore_compound_types
        )


# Adapted from https://github.com/Mergifyio/daiquiri/blob/main/daiquiri/formatter.py
@dataclass
class HumanFormatter(Formatter):
    """Formatter for a "human" output.

    Extra keywords are merged into a `{extra}` placeholder by a `stlog.formatter.KVFormatter`.

    If you use this placeholder on your `fmt`, any keywords
    passed to a logging call will be formatted into a "extras" string and
    included in a logging message.

    Example::

        logger.info("my message", foo="bar", foo2=123)

    will cause an "extras" string of::

        {foo=bar foo2=123}

    You can change the way the `{extra}` placeholder is formatted
    by providing a KVFormatter object.

    Attributes:
        include_reserved_attrs_in_extras: automatical include some reserved
            logrecord attributes in "extras" (example: `["process", "thread"]`).
        kvs_formatter: key values special formatter for formatting `{extra}`
            placeholder.

    """

    include_reserved_attrs_in_extras: Sequence[str] = field(default_factory=list)
    kvs_formatter: KVFormatter = field(default_factory=LogFmtKVFormatter)

    def _make_extras_string(self, record: logging.LogRecord) -> str:
        if not hasattr(record, STLOG_EXTRA_KEY):
            return ""
        kvs: dict[str, Any] = {}
        for k in list(getattr(record, STLOG_EXTRA_KEY)) + list(
            self.include_reserved_attrs_in_extras
        ):
            key = self._make_extra_key_name(k)
            if key:
                kvs[key] = getattr(record, k)
        return self.kvs_formatter.format(kvs)

    def _add_extras(self, record: logging.LogRecord) -> None:
        record.extras = self._make_extras_string(record)

    def _remove_extras(self, record: logging.LogRecord) -> None:
        delattr(record, "extras")

    def format(self, record: logging.LogRecord) -> str:
        self._add_extras(record)
        s = super().format(record)
        self._remove_extras(record)
        return s


@dataclass
class RichHumanFormatter(HumanFormatter):
    fmt: str | None = DEFAULT_STLOG_RICH_HUMAN_FORMAT
    kvs_formatter: KVFormatter = field(default_factory=RichLogFmtKVFormatter)

    def _add_extras(self, record: logging.LogRecord) -> None:
        super()._add_extras(record)
        record.rich_escaped_message = rich_markup_escape(record.getMessage())
        record.rich_escaped_extras = rich_markup_escape(record.extras)  # type: ignore
        level = record.levelname.lower()
        if level in ["notset", "debug", "info", "critical"]:
            record.rich_level_style = "logging.level.%s" % level
        elif level == "warning":
            record.rich_level_style = "logging.level.error"
        elif level == "error":
            record.rich_level_style = "logging.level.critical"
        else:
            record.rich_level_style = "logging.level.none"

    def _remove_extras(self, record: logging.LogRecord) -> None:
        delattr(record, "rich_escaped_message")
        delattr(record, "rich_level_style")
        delattr(record, "rich_escaped_extras")
        super()._remove_extras(record)

    def formatException(self, ei):  # noqa: N802
        return ""

    def formatStack(self, stack_info):  # noqa: N802
        return ""


def json_formatter_default_extra_key_rename_fn(key: str) -> str | None:
    """Simple "extra_key_rename" function to remove leading underscores."""
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
    indent: int | None = None
    sort_keys: bool = True

    def json_serialize(self, message_dict: dict[str, Any]) -> str:
        return json.dumps(
            message_dict,
            indent=self.indent,
            sort_keys=self.sort_keys,
            default=_truncate_serialize,
        )

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
