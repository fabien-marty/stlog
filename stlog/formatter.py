from __future__ import annotations

import fnmatch
import importlib
import json
import logging
import re
import traceback
import typing
from collections import OrderedDict
from datetime import date, datetime, time, timezone
from inspect import istraceback
from time import gmtime
from typing import Any, Sequence

from stlog.base import STLOG_EXTRA_KEYS_KEY, ExtrasLogRecord

DEFAULT_STLOG_HUMAN_FORMAT = (
    "%(asctime)s %(slevel_name)-10.10s %(name)s#%(process)d: %(message)s %(extras)s"
)
DEFAULT_STLOG_RICH_FORMAT = "%(name)s#%(process)d: %(message)s %(extras)s"


# Lightly adapter from https://github.com/Mergifyio/daiquiri/blob/main/daiquiri/formatter.py
class StLogFormatter(logging.Formatter):
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
        *args: typing.Any,
        **kwargs: typing.Any,
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
        super().__init__(*args, **kwargs)

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

    def format(self, record: logging.LogRecord) -> str:
        record = typing.cast(ExtrasLogRecord, record)
        self.add_extras(record)
        s = super().format(record)
        self.remove_extras(record)
        return s


class UTCHumanFormatter(StLogFormatter):
    converter = gmtime


HUMAN_FORMATTER = UTCHumanFormatter(
    fmt=DEFAULT_STLOG_HUMAN_FORMAT, datefmt="%Y-%m-%d %H:%M:%S (utc)"
)
RICH_FORMATTER = UTCHumanFormatter(
    fmt=DEFAULT_STLOG_RICH_FORMAT, datefmt="%Y-%m-%d %H:%M:%S (utc)"
)


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


# Stolen from https://github.com/madzak/python-json-logger/blob/master/src/pythonjsonlogger/jsonlogger.py
def merge_record_extra(
    record: logging.LogRecord,
    target: dict,
    reserved: dict | list,
    rename_fields: dict[str, str] | None = None,
) -> dict:
    """
    Merges extra attributes from LogRecord object into target dictionary
    :param record: logging.LogRecord
    :param target: dict to update
    :param reserved: dict or list with reserved keys to skip
    :param rename_fields: an optional dict, used to rename field names in the output.
            Rename levelname to log.level: {'levelname': 'log.level'}
    """
    if rename_fields is None:
        rename_fields = {}
    for key, value in record.__dict__.items():
        # this allows to have numeric keys
        if key not in reserved and not (
            hasattr(key, "startswith") and key.startswith("_")
        ):
            target[rename_fields.get(key, key)] = value
    return target


# Stolen from https://github.com/madzak/python-json-logger/blob/master/src/pythonjsonlogger/jsonlogger.py
class JsonEncoder(json.JSONEncoder):
    """
    A custom encoder extending the default JSONEncoder
    """

    def default(self, obj):
        if isinstance(obj, (date, datetime, time)):
            return self.format_datetime_obj(obj)

        elif istraceback(obj):
            return "".join(traceback.format_tb(obj)).strip()

        elif type(obj) == Exception or isinstance(obj, Exception) or type(obj) == type:
            return str(obj)

        try:
            return super().default(obj)

        except TypeError:
            try:
                return str(obj)

            except Exception:
                return None

    def format_datetime_obj(self, obj):
        return obj.isoformat()


# Stolen from https://github.com/madzak/python-json-logger/blob/master/src/pythonjsonlogger/jsonlogger.py
class JsonFormatter(logging.Formatter):
    """
    A custom formatter to format logging records as json strings.
    Extra values will be formatted as str() if not supported by
    json default encoder
    """

    def __init__(self, *args, **kwargs):
        """
        :param json_default: a function for encoding non-standard objects
            as outlined in https://docs.python.org/3/library/json.html
        :param json_encoder: optional custom encoder
        :param json_serializer: a :meth:`json.dumps`-compatible callable
            that will be used to serialize the log record.
        :param json_indent: an optional :meth:`json.dumps`-compatible numeric value
            that will be used to customize the indent of the output json.
        :param prefix: an optional string prefix added at the beginning of
            the formatted string
        :param rename_fields: an optional dict, used to rename field names in the output.
            Rename message to @message: {'message': '@message'}
        :param static_fields: an optional dict, used to add fields with static values to all logs
        :param json_indent: indent parameter for json.dumps
        :param json_ensure_ascii: ensure_ascii parameter for json.dumps
        :param reserved_attrs: an optional list of fields that will be skipped when
            outputting json log record. Defaults to all log record attributes:
            http://docs.python.org/library/logging.html#logrecord-attributes
        :param timestamp: an optional string/boolean field to add a timestamp when
            outputting the json log record. If string is passed, timestamp will be added
            to log record using string as key. If True boolean is passed, timestamp key
            will be "timestamp". Defaults to False/off.
        """
        self.json_default = self._str_to_fn(kwargs.pop("json_default", None))
        self.json_encoder = self._str_to_fn(kwargs.pop("json_encoder", None))
        self.json_serializer = self._str_to_fn(
            kwargs.pop("json_serializer", json.dumps)
        )
        self.json_indent = kwargs.pop("json_indent", None)
        self.json_ensure_ascii = kwargs.pop("json_ensure_ascii", True)
        self.prefix = kwargs.pop("prefix", "")
        self.rename_fields = kwargs.pop("rename_fields", {})
        self.static_fields = kwargs.pop("static_fields", {})
        reserved_attrs = kwargs.pop("reserved_attrs", RESERVED_ATTRS)
        self.reserved_attrs = dict(zip(reserved_attrs, reserved_attrs))
        self.timestamp = kwargs.pop("timestamp", False)

        # super(JsonFormatter, self).__init__(*args, **kwargs)
        logging.Formatter.__init__(self, *args, **kwargs)
        if not self.json_encoder and not self.json_default:
            self.json_encoder = JsonEncoder

        self._required_fields = self.parse()
        self._skip_fields = dict(zip(self._required_fields, self._required_fields))
        self._skip_fields.update(self.reserved_attrs)

    def _str_to_fn(self, fn_as_str):
        """
        If the argument is not a string, return whatever was passed in.
        Parses a string such as package.module.function, imports the module
        and returns the function.
        :param fn_as_str: The string to parse. If not a string, return it.
        """
        if not isinstance(fn_as_str, str):
            return fn_as_str

        path, _, function = fn_as_str.rpartition(".")
        module = importlib.import_module(path)
        return getattr(module, function)

    def parse(self) -> list[str]:
        """
        Parses format string looking for substitutions
        This method is responsible for returning a list of fields (as strings)
        to include in all log messages.
        """
        if isinstance(self._style, logging.StringTemplateStyle):
            formatter_style_pattern = re.compile(r"\$\{(.+?)\}", re.IGNORECASE)
        elif isinstance(self._style, logging.StrFormatStyle):
            formatter_style_pattern = re.compile(r"\{(.+?)\}", re.IGNORECASE)
        # PercentStyle is parent class of StringTemplateStyle and StrFormatStyle so
        # it needs to be checked last.
        elif isinstance(self._style, logging.PercentStyle):
            formatter_style_pattern = re.compile(r"%\((.+?)\)", re.IGNORECASE)
        else:
            raise ValueError("Invalid format: %s" % self._fmt)

        if self._fmt:
            return formatter_style_pattern.findall(self._fmt)
        else:
            return []

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """
        Override this method to implement custom logic for adding fields.
        """
        for field in self._required_fields:
            log_record[field] = record.__dict__.get(field)

        log_record.update(self.static_fields)
        log_record.update(message_dict)
        merge_record_extra(
            record,
            log_record,
            reserved=self._skip_fields,
            rename_fields=self.rename_fields,
        )

        if self.timestamp:
            key = self.timestamp if type(self.timestamp) == str else "timestamp"
            log_record[key] = datetime.fromtimestamp(record.created, tz=timezone.utc)

        self._perform_rename_log_fields(log_record)

    def _perform_rename_log_fields(self, log_record):
        for old_field_name, new_field_name in self.rename_fields.items():
            log_record[new_field_name] = log_record[old_field_name]
            del log_record[old_field_name]

    def process_log_record(self, log_record):
        """
        Override this method to implement custom logic
        on the possibly ordered dictionary.
        """
        return log_record

    def jsonify_log_record(self, log_record):
        """Returns a json string of the log record."""
        return self.json_serializer(
            log_record,
            default=self.json_default,
            cls=self.json_encoder,
            indent=self.json_indent,
            ensure_ascii=self.json_ensure_ascii,
        )

    def serialize_log_record(self, log_record: dict[str, Any]) -> str:
        """Returns the final representation of the log record."""
        return f"{self.prefix}{self.jsonify_log_record(log_record)}"

    def format(self, record: logging.LogRecord) -> str:
        """Formats a log record and serializes to json"""
        message_dict: dict[str, Any] = {}
        # FIXME: logging.LogRecord.msg and logging.LogRecord.message in typeshed
        #        are always type of str. We shouldn't need to override that.
        if isinstance(record.msg, dict):
            message_dict = record.msg
            record.message = ""
        else:
            record.message = record.getMessage()
        # only format time if needed
        if "asctime" in self._required_fields:
            record.asctime = self.formatTime(record, self.datefmt)

        # Display formatted exception, but allow overriding it in the
        # user-supplied dict.
        if record.exc_info and not message_dict.get("exc_info"):
            message_dict["exc_info"] = self.formatException(record.exc_info)
        if not message_dict.get("exc_info") and record.exc_text:
            message_dict["exc_info"] = record.exc_text
        # Display formatted record of stack frames
        # default format is a string returned from :func:`traceback.print_stack`
        if record.stack_info and not message_dict.get("stack_info"):
            message_dict["stack_info"] = self.formatStack(record.stack_info)

        log_record: dict[str, Any] = OrderedDict()
        self.add_fields(log_record, record, message_dict)
        log_record = self.process_log_record(log_record)

        return self.serialize_log_record(log_record)


class DatadogFormatter(JsonFormatter):  # type: ignore[misc]
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


DATADOG_FORMATTER = DatadogFormatter()
