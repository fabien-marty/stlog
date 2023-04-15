from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from stlog.base import check_env_true, logfmt_format

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
