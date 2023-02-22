from __future__ import annotations

import logging

from standard_structlog.base import STLOG_MANAGED_KEY
from standard_structlog.context import ExecutionLogContext


class ContextReinjectHandlerWrapper:
    def __init__(self, wrapped: logging.Handler):
        self._wrapped = wrapped

    def handle(self, record):
        if not getattr(record, STLOG_MANAGED_KEY, False):
            # the context is not already injected in record
            # (this log didn't pass by stlog ContextVarsAdapter)
            # => let's fix that
            new_kwargs = {**ExecutionLogContext._get(), STLOG_MANAGED_KEY: True}
            daiquiri_extra_keys: set[str] = getattr(
                record, "_daiquiri_extra_keys", set()
            )
            for k, v in new_kwargs.items():
                setattr(record, k, v)
                daiquiri_extra_keys.add(k)
            record._daiquiri_extra_keys = daiquiri_extra_keys
        self._wrapped.handle(record)

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        # Wraps other calls to real handler
        return getattr(self._wrapped, attr)
