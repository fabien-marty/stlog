from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from stlog.base import check_env_true, logfmt_format_value

STLOG_DEFAULT_IGNORE_COMPOUND_TYPES = check_env_true(
    "STLOG_IGNORE_COMPOUND_TYPES", True
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


@dataclass
class KVFormatter(ABC):
    """Abstract base class to format extras key-values.

    Attributes:
        value_max_serialized_length: maximum size of extra values to be included in `{extras}` placeholder
            (after this limit, the value will be truncated and ... will be added at the end, 0 means "no limit",
            default: 40).

    """

    value_max_serialized_length: int | None = None

    def __post_init__(self):
        if self.value_max_serialized_length is None:
            self.value_max_serialized_length = 40

    def _serialize_value(self, v: Any) -> str:
        return _truncate_serialize(
            v,
            self.value_max_serialized_length
            if self.value_max_serialized_length is not None
            else 40,
        )

    @abstractmethod
    def format(self, kvs: dict[str, Any]) -> str:
        pass


@dataclass
class EmptyKVFormatter(KVFormatter):
    """Class to format extra key-values as an empty string."""

    def format(self, kvs: dict[str, Any]) -> str:
        return ""


# Adapted from https://github.com/Mergifyio/daiquiri/blob/main/daiquiri/formatter.py
@dataclass
class TemplateKVFormatter(KVFormatter):
    """Class to format extra key-values as a string with templates.

    Example::

        {foo="bar", foo2=123}

    will be formatted as:

        [foo: bar] [foo2: 123]

    Attributes:
        template: the template to format a key/value:
            `{key}` placeholder is the key, `{value}` is the value
            (default to `"{key}={value}"`)
        separator: the separator between multiple key/values
        prefix: the prefix before key/value parts.
        suffix: the suffix after key/values parts.
        ignore_compound_types: if set to False, accept compound types (dict, list) as values (they will be
            serialized using their default string serialization method)

    """

    template: str | None = None
    separator: str = ", "
    prefix: str = " {"
    suffix: str = "}"
    ignore_compound_types: bool = STLOG_DEFAULT_IGNORE_COMPOUND_TYPES

    def __post_init__(self):
        if self.template is None:
            self.template = "{key}={value}"
        return super().__post_init__()

    def format(self, kvs: dict[str, Any]) -> str:
        res: str = ""
        tmp: list[str] = []
        for k, v in sorted(kvs.items(), key=lambda x: x[0]):
            if self.ignore_compound_types and isinstance(v, (dict, list, set)):
                continue
            assert self.template is not None
            tmp.append(self.template.format(key=k, value=self._serialize_value(v)))
        res = self.separator.join(tmp)
        if res != "":
            res = self.prefix + res + self.suffix
        return res


@dataclass
class LogFmtKVFormatter(TemplateKVFormatter):
    """Class to format extra key-values as a LogFmt string.

    Example::

        {foo="bar", foo2=123, foo3="string with a space"}

    will be formatted as:

        foo=bar, foo2=123, foo3="string with a space"


    Note: `template` and `separator` are automatically set/forced.

    """

    def __post_init__(self):
        self.separator = " "
        if self.template is None:
            self.template = "{key}={value}"
        if self.value_max_serialized_length is None:
            self.value_max_serialized_length = 0
        return super().__post_init__()

    def _serialize_value(self, v: Any) -> str:
        return logfmt_format_value(super()._serialize_value(v))


@dataclass
class JsonKVFormatter(KVFormatter):
    """Class to format extra key-values as a JSON string.

    Attributes:
        indent: if set as a positive integer, use this number of spaces to indent the output.
            (warning: if you use this KVFormatter
            through a JSONFormatter, this parameter can be overriden at the Formatter level).
        sort_keys: if True (default), sort keys (warning: if you use this KVFormatter
            through a JSONFormatter, this parameter can be overriden at the Formatter level).
    """

    indent: int | None = None
    sort_keys: bool = True

    def __post_init__(self):
        if self.value_max_serialized_length is None:
            self.value_max_serialized_length = 0  # no limit
        self.separator = " "
        self.template = "{key}={value}"
        return super().__post_init__()

    def format(self, kvs: dict[str, Any]) -> str:
        return json.dumps(
            kvs,
            sort_keys=self.sort_keys,
            default=self._serialize_value,
            indent=self.indent,
        )
