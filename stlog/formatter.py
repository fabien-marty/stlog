from __future__ import annotations

import fnmatch
import json
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from stlog.base import (
    GLOBAL_LOGGING_CONFIG,
    STLOG_EXTRA_KEY,
    format_string,
    logfmt_format_value,
    parse_format,
    rich_markup_escape,
)
from stlog.kvformatter import (
    JsonKVFormatter,
    KVFormatter,
    LogFmtKVFormatter,
    _truncate_serialize,
    _truncate_str,
)

DEFAULT_STLOG_HUMAN_FORMAT = "{asctime} {name} [{levelname:^10s}] {message}{extras}"
DEFAULT_STLOG_RICH_HUMAN_FORMAT = ":arrow_forward: [log.time]{asctime}[/log.time] {name} [{rich_level_style}]{levelname:^8s}[/{rich_level_style}] [bold]{rich_escaped_message}[/bold]{extras}"
DEFAULT_STLOG_LOGFMT_FORMAT = (
    "time={asctime} logger={name} level={levelname} message={message}{extras}"
)
DEFAULT_STLOG_JSON_FORMAT = """
{{
    "time": {asctime},
    "logger": {name},
    "level": {levelname},
    "message": {message},
    "source": {{
        "path": {pathname},
        "lineno": {lineno},
        "module": {module},
        "funcName": {funcName},
        "process": {process},
        "processName": {processName},
        "thread": {thread},
        "threadName": {threadName}
    }}
}}
"""
DEFAULT_STLOG_GCP_JSON_FORMAT = """
{{
    "timestamp": {asctime},
    "logger": {name},
    "severity": {levelname},
    "message": {message},
    "source": {{
        "path": {pathname},
        "lineno": {lineno},
        "module": {module},
        "funcName": {funcName},
        "process": {process},
        "processName": {processName},
        "thread": {thread},
        "threadName": {threadName}
    }}
}}
"""
DEFAULT_STLOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _unit_tests_converter(val: float | None) -> time.struct_time:
    # always the same value
    return time.gmtime(1680101317)


@dataclass
class Formatter(logging.Formatter):
    """Abstract base class for `stlog` formatters.

    Attributes:
        fmt: the default format for the formatter.
        datefmt: the format to use for `{asctime}` placeholder.
        style: can be '%', '{' or '$' to select how the format string will be merged with its data
            (see https://docs.python.org/3/library/logging.html#logging.Formatter for details)
        include_extras_keys_fnmatchs: fnmatch patterns list for including keys in `{extras}` placeholder.
        exclude_extras_keys_fnmatchs: fnmatch patterns list for excluding keys in `{extras}` placeholder.
        extra_key_rename_fn: callable which takes a key name and return a renamed key to use
            (or None to ignore the key/value).
        extra_key_max_length: maximum size of extra keys to be included in `{extras}` placeholder
            (after this limit, the value will be truncated and ... will be added at the end, 0 means "no limit").
        converter: time converter function (use `time.gmtime` (default) for UTC date/times, use `time.time`
            for local date/times), if you change the default, please change also `datefmt` keyword.
        kv_formatter: key values special formatter for formatting `{extras}`
            placeholder.
        include_reserved_attrs_in_extras: automatical include some reserved
            logrecord attributes in "extras" (example: `["process", "thread"]`).

    """

    fmt: str | None = None
    datefmt: str | None = DEFAULT_STLOG_DATE_FORMAT
    style: str = "{"
    include_extras_keys_fnmatchs: Sequence[str] | None = None
    exclude_extras_keys_fnmatchs: Sequence[str] | None = None
    extra_key_rename_fn: Callable[[str], str | None] | None = None
    extra_key_max_length: int | None = None
    converter: Callable[[float | None], time.struct_time] = time.gmtime
    kv_formatter: KVFormatter | None = None
    include_reserved_attrs_in_extras: Sequence[str] = field(default_factory=list)
    _placeholders_in_fmt: list[str] | None = field(
        init=False, default=None, repr=False, compare=False
    )

    def __post_init__(self):
        super().__init__(  # explicit call because logging.Formatter is not a dataclass
            fmt=self.fmt,
            datefmt=self.datefmt,
            style=self.style,  # type: ignore
        )
        if self.extra_key_max_length is None:
            self.extra_key_max_length = 32
        self.include_extra_keys_patterns: list[re.Pattern] = [
            re.compile(fnmatch.translate("*"))
        ]  # all by default
        self.exclude_extra_keys_patterns: list[re.Pattern] = []  # empty by default
        if self.include_extras_keys_fnmatchs is not None:
            self.include_extra_keys_patterns = [
                re.compile(fnmatch.translate(x))
                for x in self.include_extras_keys_fnmatchs
            ]
        if self.exclude_extras_keys_fnmatchs is not None:
            self.exclude_extra_keys_patterns = [
                re.compile(fnmatch.translate(x))
                for x in self.exclude_extras_keys_fnmatchs
            ]
        if GLOBAL_LOGGING_CONFIG._unit_tests_mode:
            self.converter = _unit_tests_converter

    @property
    def placeholders_in_fmt(self) -> list[str]:
        if self._placeholders_in_fmt is None:
            self._placeholders_in_fmt = parse_format(self.fmt, self.style)
        return self._placeholders_in_fmt

    def _make_extras_string(
        self, record: logging.LogRecord, extra_kvs: dict[str, Any] | None = None
    ) -> str:
        if self.kv_formatter is None:
            return ""
        if not hasattr(record, STLOG_EXTRA_KEY):
            return ""
        kvs: dict[str, Any] = {}
        for k in list(getattr(record, STLOG_EXTRA_KEY)) + list(
            self.include_reserved_attrs_in_extras
        ):
            key = self._make_extra_key_name(k)
            if key:
                kvs[key] = getattr(record, k)
        if extra_kvs:
            kvs.update(extra_kvs)
        return self.kv_formatter.format(kvs)

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
        return _truncate_str(
            new_extra_key,
            self.extra_key_max_length if self.extra_key_max_length is not None else 0,
        )

    def format(self, record: logging.LogRecord) -> str:
        if GLOBAL_LOGGING_CONFIG._unit_tests_mode:
            # FIXME: it would be better as a Filter, wouldn't be?
            # fix some fields in record to get always the same values
            record.filename = "filename.py"
            record.pathname = "/path/filename.py"
            record.thread = 12345
            record.process = 6789
            record.processName = "MainProcess"
            record.threadName = "MainThread"
        return super().format(record)


# Adapted from https://github.com/Mergifyio/daiquiri/blob/main/daiquiri/formatter.py
@dataclass
class HumanFormatter(Formatter):
    """Formatter for a "human" output.

    Extra keywords are merged into a `{extras}` placeholder by a `stlog.kvformatter.KVFormatter`.

    If you use this placeholder on your `fmt`, any keywords
    passed to a logging call will be formatted into a "extras" string and
    included in a logging message.

    Example::

        logger.info("my message", foo="bar", foo2=123)

    will cause an "extras" string of::

        {foo=bar foo2=123}

    You can change the way the `{extras}` placeholder is formatted
    by providing a KVFormatter object.

    """

    def __post_init__(self):
        if self.fmt is None:
            self.fmt = DEFAULT_STLOG_HUMAN_FORMAT
        if self.kv_formatter is None:
            self.kv_formatter = LogFmtKVFormatter()
        if self.exclude_extras_keys_fnmatchs is None:
            self.exclude_extras_keys_fnmatchs = ("_*",)
        super().__post_init__()

    def _add_extras(self, record: logging.LogRecord) -> None:
        record.extras = self._make_extras_string(record)

    def _remove_extras(self, record: logging.LogRecord) -> None:
        delattr(record, "extras")

    def format(self, record: logging.LogRecord) -> str:
        if "extras" in self.placeholders_in_fmt:
            self._add_extras(record)
        s = super().format(record)
        if "extras" in self.placeholders_in_fmt:
            self._remove_extras(record)
        return s


@dataclass
class RichHumanFormatter(HumanFormatter):
    def __post_init__(self):
        if self.kv_formatter is None:
            self.kv_formatter = LogFmtKVFormatter(
                prefix="\n    :arrow_right_hook: ",
                suffix="",
                template="[repr.attrib_name]{key}[/repr.attrib_name][repr.attrib_equal]=[/repr.attrib_equal][repr.attrib_value]{value}[/repr.attrib_value]",
            )
        if self.fmt is None:
            self.fmt = DEFAULT_STLOG_RICH_HUMAN_FORMAT
        super().__post_init__()

    def _add_extras(self, record: logging.LogRecord) -> None:
        super()._add_extras(record)
        record.rich_escaped_message = rich_markup_escape(record.getMessage())
        record.rich_escaped_extras = rich_markup_escape(record.extras)  # type: ignore
        level = record.levelname.lower()
        if level in ["notset", "debug", "info", "critical"]:
            record.rich_level_style = f"logging.level.{level}"
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
class LogFmtFormatter(Formatter):
    exc_info_key: str | None = "exc_info"
    stack_info_key: str | None = "stack_info"

    def __post_init__(self):
        if self.kv_formatter is None:
            self.kv_formatter = LogFmtKVFormatter(prefix=" ", suffix="")
        if self.fmt is None:
            self.fmt = DEFAULT_STLOG_LOGFMT_FORMAT
        if self.extra_key_max_length is None:
            self.extra_key_max_length = 0
        super().__post_init__()

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        record_dict: dict[str, Any] = {
            k: logfmt_format_value(getattr(record, k))
            for k in self.placeholders_in_fmt
            if k != "extras"
        }
        extra_kvs: dict[str, Any] = {}
        if self.exc_info_key:
            if record.exc_info:
                extra_kvs[self.exc_info_key] = self.formatException(record.exc_info)
            elif record.exc_text:
                extra_kvs[self.exc_info_key] = record.exc_text
        if self.stack_info_key and record.stack_info:
            extra_kvs[self.stack_info_key] = self.formatStack(record.stack_info)
        if "extras" in self.placeholders_in_fmt:
            record_dict["extras"] = self._make_extras_string(
                record, extra_kvs=extra_kvs
            )
        return format_string(self.fmt, self.style, record_dict)


@dataclass
class JsonFormatter(Formatter):
    """Formatter for a JSON / parsing friendly output."""

    indent: int | None = None
    sort_keys: bool = True
    include_extras_in_key: str | None = ""
    exc_info_key: str | None = "exc_info"
    stack_info_key: str | None = "stack_info"

    def __post_init__(self):
        if self.extra_key_max_length is None:
            self.extra_key_max_length = 0
        if self.kv_formatter is None:
            # note: no need to sort/indent here as it will be sorted/indented at this level
            self.kv_formatter = JsonKVFormatter(sort_keys=False, indent=False)
        if self.fmt is None:
            self.fmt = DEFAULT_STLOG_JSON_FORMAT
        if self.extra_key_rename_fn is None:
            self.extra_key_rename_fn = json_formatter_default_extra_key_rename_fn
        super().__post_init__()

    def json_serialize(self, message_dict: dict[str, Any]) -> str:
        return json.dumps(
            message_dict,
            indent=self.indent,
            sort_keys=self.sort_keys,
            default=_truncate_serialize,
        )

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)
        record_dict: dict[str, Any] = {
            k: json.dumps(getattr(record, k))
            for k in self.placeholders_in_fmt
            if k != "extras"
        }
        s = format_string(self.fmt, self.style, record_dict)
        obj = json.loads(s)
        if self.include_extras_in_key is not None:
            extras_str = self._make_extras_string(record)
            if extras_str:
                extras_obj = json.loads(extras_str)
                if self.include_extras_in_key == "":
                    for key, value in extras_obj.items():
                        if key not in obj:
                            obj[key] = value
                else:
                    obj[self.include_extras_in_key] = extras_obj
        if self.exc_info_key:
            if record.exc_info:
                obj[self.exc_info_key] = self.formatException(record.exc_info)
            elif record.exc_text:
                obj[self.exc_info_key] = record.exc_text
        if self.stack_info_key and record.stack_info:
            obj[self.stack_info_key] = self.formatStack(record.stack_info)
        return self.json_serialize(obj)
