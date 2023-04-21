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
    """Abstract base class to format extras key-values."""

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

    Extra keywords are merged into a `{extra}` placeholder.

    Example::

        {foo="bar", foo2=123}

    will be formatted as:

        [foo: bar] [foo2: 123]

    Attributes:
        template: the template to format a key/value:
            `{key}` placeholder is the key, `{value}` is the value.
        separator: the separator between multiple key/values.
        prefix: the prefix before key/value parts.
        suffix: the suffix after key/values parts.
        value_max_serialized_length: maximum size of extra values to be included in `{extra}` placeholder
            (after this limit, the value will be truncated and ... will be added at the end, 0 means "no limit").
        ignore_compound_types: FIXME

    """

    template: str = "{key}={value}"
    separator: str = ", "
    prefix: str = " {"
    suffix: str = "}"
    value_max_serialized_length: int = 40
    ignore_compound_types: bool = STLOG_DEFAULT_IGNORE_COMPOUND_TYPES

    def serialize_value(self, v: Any) -> str:
        return _truncate_serialize(v, self.value_max_serialized_length)

    def format(self, kvs: dict[str, Any]) -> str:
        res: str = ""
        tmp: list[str] = []
        for k, v in sorted(kvs.items(), key=lambda x: x[0]):
            if self.ignore_compound_types and isinstance(v, (dict, list, set)):
                continue
            tmp.append(self.template.format(key=k, value=self.serialize_value(v)))
        res = self.separator.join(tmp)
        if res != "":
            res = self.prefix + res + self.suffix
        return res


@dataclass
class LogFmtKVFormatter(TemplateKVFormatter):
    """FIXME"""

    separator: str = " "
    template: str = "{key}={value}"

    def serialize_value(self, v: Any) -> str:
        return logfmt_format_value(super().serialize_value(v))


@dataclass
class JsonKVFormatter(KVFormatter):
    """FIXME"""

    sort_keys: bool = True

    def format(self, kvs: dict[str, Any]) -> str:
        return json.dumps(kvs, sort_keys=self.sort_keys)
