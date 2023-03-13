from __future__ import annotations

import fnmatch
import logging
import re
import time
import typing
from typing import Any, Callable, Literal, Sequence

from stlog._json_formatter import _JsonFormatter
from stlog.base import STLOG_EXTRA_KEY

DEFAULT_STLOG_HUMAN_FORMAT = (
    "%(asctime)s %(slevel_name)-10.10s %(name)s#%(process)d: %(message)s %(extras)s"
)
DEFAULT_STLOG_RICH_FORMAT = "%(name)s#%(process)d: %(message)s %(extras)s"
DEFAULT_STLOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class _Formatter(logging.Formatter):
    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = DEFAULT_STLOG_DATE_FORMAT,
        style: Literal["%", "{", "$"] = "%",
        validate: bool = True,
        *,
        include_extras_keys_fnmatchs: Sequence[str] = ("*",),
        exclude_extras_keys_fnmatchs: Sequence[str] = ("_*",),
        converter: Callable[[float | None], time.struct_time] = time.gmtime,
    ):
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            validate=validate,
        )
        self.include_extra_keys_patterns: list[re.Pattern] = [
            re.compile(fnmatch.translate(x)) for x in include_extras_keys_fnmatchs
        ]
        self.exclude_extra_keys_patterns: list[re.Pattern] = [
            re.compile(fnmatch.translate(x)) for x in exclude_extras_keys_fnmatchs
        ]
        self.converter: Callable[[float | None], time.struct_time] = converter

    def _use_extra_key(self, extra_key: str) -> bool:
        for pattern in self.include_extra_keys_patterns:
            if re.match(pattern, extra_key):
                break
        else:
            # not found
            return False
        for pattern in self.exclude_extra_keys_patterns:
            if re.match(pattern, extra_key):
                return False
        return True


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
        include_extras_keys_fnmatchs: fnmatch patterns list for including keys in `%(extras)s` placeholder.
        exclude_extras_keys_fnmatchs: fnmatch patterns list for excluding keys in `%(extras)s` placeholder.
        extra_value_serialized_types: accepted value types for including the key/value in `%(extras)s` placeholder.
        extra_key_max_length: maximum size of extra keys to be included in `%(extras)s` placeholder
            (after this limit, the value will be truncated and ... will be added at the end, 0 means "no limit").
        extra_value_max_serialized_length: maximum size of extra values to be included in `%(extras)s` placeholder
            (after this limit, the value will be truncated and ... will be added at the end, 0 means "no limit").
        converter: time converter function (use `time.gmtime` (default) for UTC date/times, use `time.time`
            for local date/times), if you change the default, please change also `datefmt` keyword.

    """

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = DEFAULT_STLOG_DATE_FORMAT,
        style: Literal["%", "{", "$"] = "%",
        validate: bool = True,
        *,
        extras_template: str = "[{0}: {1}]",
        extras_separator: str = " ",
        extras_prefix: str = " ",
        extras_suffix: str = "",
        include_extras_keys_fnmatchs: Sequence[str] = ("*",),
        exclude_extras_keys_fnmatchs: Sequence[str] = ("_*",),
        extra_value_serialized_types: tuple = (
            int,
            bool,
            str,
            bytes,
            float,
        ),
        extra_key_max_length: int = 32,
        extra_value_max_serialized_length: int = 40,
    ) -> None:
        super().__init__(
            fmt=fmt,
            datefmt=datefmt,
            style=style,
            validate=validate,
            exclude_extras_keys_fnmatchs=exclude_extras_keys_fnmatchs,
            include_extras_keys_fnmatchs=include_extras_keys_fnmatchs,
        )
        self.extras_template = extras_template
        self.extras_separator = extras_separator
        self.extras_prefix = extras_prefix
        self.extras_suffix = extras_suffix
        self.extra_key_max_length = extra_key_max_length
        self.extra_value_max_serialized_length = extra_value_max_serialized_length
        self.extra_value_serialized_types = extra_value_serialized_types

    def _limit_extra_key(self, extra_key: str) -> str:
        if self.extra_key_max_length <= 0:
            return extra_key
        if len(extra_key) > self.extra_key_max_length:
            return extra_key[0 : (self.extra_key_max_length - 3)] + "..."
        return extra_key

    def _serialize_extra_value(self, extra_value: Any) -> str | None:
        if extra_value is not None and not isinstance(
            extra_value, self.extra_value_serialized_types
        ):
            return None
        try:
            serialized = str(extra_value)
        except Exception:
            return "[can't serialize]"
        if self.extra_value_max_serialized_length <= 0:
            return serialized
        if len(serialized) > self.extra_value_max_serialized_length:
            return serialized[0 : (self.extra_value_max_serialized_length - 3)] + "..."
        return serialized

    def add_extras(self, record: logging.LogRecord) -> None:
        record.slevel_name = f"[{record.levelname}]"
        if not hasattr(record, STLOG_EXTRA_KEY):
            record.extras = ""
            return
        tmp = []
        for k in getattr(record, STLOG_EXTRA_KEY):
            if not self._use_extra_key(k):
                continue
            serialized = self._serialize_extra_value(getattr(record, k))
            if serialized is None:
                continue
            tmp.append(
                self.extras_template.format(self._limit_extra_key(k), serialized)
            )
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


class JsonFormatter(_JsonFormatter):
    """Formatter for a JSON / parsing friendly output."""

    def __init__(self) -> None:
        super().__init__(timestamp=True)

    def add_fields(
        self,
        log_record: dict[str, typing.Any],
        record: logging.LogRecord,
        message_dict: dict[str, str],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["status"] = record.levelname.lower()
        log_record["logger"] = {
            "name": record.name,
        }
        log_record["source"] = {
            "path": record.pathname,
            "lineno": record.lineno,
        }
        if record.exc_info and record.exc_info[0]:
            log_record["error"] = {
                "kind": record.exc_info[0].__name__,
                "stack": message_dict.get("stack_info"),
                "message": message_dict.get("exc_info"),
            }
            log_record.pop("exc_info", None)
            log_record.pop("stack_info", None)
