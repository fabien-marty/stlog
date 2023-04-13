from __future__ import annotations

import fnmatch
import logging
import re
import time
import typing
from typing import Any, Callable, Literal, Sequence

from stlog._json_formatter import _JsonFormatter
from stlog.base import STLOG_EXTRA_KEYS_KEY, ExtrasLogRecord

DEFAULT_STLOG_HUMAN_FORMAT = (
    "%(asctime)s %(slevel_name)-10.10s %(name)s#%(process)d: %(message)s %(extras)s"
)
DEFAULT_STLOG_RICH_FORMAT = "%(name)s#%(process)d: %(message)s %(extras)s"
DEFAULT_STLOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S (utc)"


# Adapted from https://github.com/Mergifyio/daiquiri/blob/main/daiquiri/formatter.py
class HumanFormatter(logging.Formatter):
    """Formats extra keywords into %(extras)s placeholder.

    Any keywords passed to a logging call will be formatted into a
    "extras" string and included in a logging message.

    Example:
        logger.info('my message', extra='keyword')

    will cause an "extras" string of:
        [extra: keyword]

    to be inserted into the format in place of %(extras)s.

    The optional `keywords` argument must be passed into the init
    function to enable this functionality. Without it normal daiquiri
    formatting will be applied. Any keywords included in the
    `keywords` parameter will not be included in the "extras" string.

    Special keywords:

    keywords
        A set of strings containing keywords to filter out of the
        "extras" string.

    extras_template
        A format string to use instead of '[{0}: {1}]'

    extras_separator
        What string to "join" multiple "extras" with.

    extras_prefix and extras_suffix
        Strings which will be prepended and appended to the "extras"
        string respectively. These will only be prepended if the
        "extras" string is not empty.
    """

    def __init__(  # noqa: PLR0913
        self,
        keywords: set[str] | None = None,
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
        fmt: str | None = None,
        datefmt: str | None = DEFAULT_STLOG_DATE_FORMAT,
        style: Literal["%", "{", "$"] = "%",
        validate: bool = True,
        converter: Callable[[float | None], time.struct_time] | None = time.gmtime,
    ) -> None:
        self.keywords = set() if keywords is None else keywords
        self.extras_template = extras_template
        self.extras_separator = extras_separator
        self.extras_prefix = extras_prefix
        self.extras_suffix = extras_suffix
        self.extra_key_max_length = extra_key_max_length
        self.extra_value_max_serialized_length = extra_value_max_serialized_length
        self.extra_value_serialized_types = extra_value_serialized_types
        self.include_extra_keys_patterns: list[re.Pattern] = [
            re.compile(fnmatch.translate(x)) for x in include_extras_keys_fnmatchs
        ]
        self.exclude_extra_keys_patterns: list[re.Pattern] = [
            re.compile(fnmatch.translate(x)) for x in exclude_extras_keys_fnmatchs
        ]
        self.fmt = fmt
        self.datefmt = datefmt
        self.style = style
        self.validate = validate
        self.__super: logging.Formatter | None = None
        self._converter: Callable[[float | None], time.struct_time] | None = converter

    @property
    def _super(self) -> logging.Formatter:
        if self.__super is None:
            self.__super = logging.Formatter(
                fmt=self.fmt,
                datefmt=self.datefmt,
                style=self.style,
                validate=self.validate,
            )
        return self.__super

    def _use_extra_key(self, extra_key: str) -> bool:
        if extra_key == STLOG_EXTRA_KEYS_KEY:
            return False
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

    def add_extras(self, record: ExtrasLogRecord) -> None:
        if not hasattr(record, STLOG_EXTRA_KEYS_KEY):
            record.extras = ""
            return
        tmp = []
        for k in getattr(record, STLOG_EXTRA_KEYS_KEY):
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
        record.slevel_name = f"[{record.levelname}]"

    def remove_extras(self, record: ExtrasLogRecord) -> None:
        del record.extras
        del record.slevel_name

    def formatTime(self, record, datefmt=None):  # noqa: N802
        return self._super.formatTime(record, datefmt=datefmt)

    def formatException(self, ei):  # noqa: N802
        return self._super.formatException(ei)

    def usesTime(self):  # noqa: N802
        return self._super.usesTime()

    def formatMessage(self, record):  # noqa: N802
        return self._super.formatMessage(record)

    def formatStack(self, stack_info):  # noqa: N802
        return self._super.formatStack(stack_info)

    def format(self, record: logging.LogRecord) -> str:
        record = typing.cast(ExtrasLogRecord, record)
        self.add_extras(record)
        s = self._super.format(record)
        self.remove_extras(record)
        return s

    @property
    def converter(self) -> Callable[[float | None], time.struct_time]:  # type: ignore
        if self._converter is None:
            return self._super.converter
        return self._converter


class JsonFormatter(_JsonFormatter):
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
        if record.exc_info and record.exc_info[0]:
            log_record["error"] = {
                "kind": record.exc_info[0].__name__,
                "stack": message_dict.get("stack_info"),
                "message": message_dict.get("exc_info"),
            }
            log_record.pop("exc_info", None)
            log_record.pop("stack_info", None)
