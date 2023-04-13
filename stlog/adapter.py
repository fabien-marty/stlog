from __future__ import annotations

import collections
import logging
import typing

from stlog.base import STLOG_EXTRA_KEYS_KEY, STLOG_MANAGED_KEY
from stlog.context import ExecutionLogContext


# ligthly adapted from https://github.com/Mergifyio/daiquiri/blob/main/daiquiri/__init__.py
class KeywordArgumentAdapter(logging.LoggerAdapter):
    """Logger adapter to add keyword arguments to log record's extra data.

    Keywords passed to the log call are added to the "extra"
    dictionary passed to the underlying logger so they are emitted
    with the log message and available to the format string.

    Special keywords:

    extra
      An existing dictionary of extra values to be passed to the
      logger. If present, the dictionary is copied and extended.

    """

    def process(
        self, msg: typing.Any, kwargs: collections.abc.MutableMapping[str, typing.Any]
    ) -> tuple[typing.Any, collections.abc.MutableMapping[str, typing.Any]]:
        # Make a new extra dictionary combining the values we were
        # given when we were constructed and anything from kwargs.
        if self.extra is not None:
            extra = dict(self.extra)
        if "extra" in kwargs:
            extra.update(kwargs.pop("extra"))
        # Move any unknown keyword arguments into the extra
        # dictionary.
        for name in list(kwargs.keys()):
            if name in ("exc_info", "stack_info"):
                continue
            extra[name] = kwargs.pop(name)
        extra[STLOG_EXTRA_KEYS_KEY] = set(extra.keys())
        kwargs["extra"] = extra
        return msg, kwargs


class ContextVarsAdapter(KeywordArgumentAdapter):
    def process(
        self, msg: typing.Any, kwargs: collections.abc.MutableMapping[str, typing.Any]
    ) -> tuple[typing.Any, collections.abc.MutableMapping[str, typing.Any]]:
        new_kwargs = {**ExecutionLogContext._get(), **kwargs, STLOG_MANAGED_KEY: True}
        return super().process(msg, new_kwargs)


def getLogger(name: str | None = None, **kwargs) -> ContextVarsAdapter:  # noqa: N802
    return ContextVarsAdapter(logging.getLogger(name), kwargs)
