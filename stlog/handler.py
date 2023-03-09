from __future__ import annotations

import logging

from stlog.base import (
    GLOBAL_LOGGING_CONFIG,
    STLOG_EXTRA_KEYS_KEY,
    STLOG_MANAGED_KEY,
)
from stlog.context import ExecutionLogContext


class ContextReinjectHandlerWrapper:
    def __init__(self, wrapped: logging.Handler):
        self._wrapped = wrapped

    def handle(self, record):
        if GLOBAL_LOGGING_CONFIG.reinject_context_in_standard_logging:
            if not getattr(record, STLOG_MANAGED_KEY, False):
                # the context is not already injected in record
                # (this log didn't pass by stlog ContextVarsAdapter)
                # => let's fix that
                new_kwargs = {**ExecutionLogContext._get(), STLOG_MANAGED_KEY: True}
                extra_keys: set[str] = getattr(record, STLOG_EXTRA_KEYS_KEY, set())
                for k, v in new_kwargs.items():
                    setattr(record, k, v)
                    extra_keys.add(k)
                setattr(record, STLOG_EXTRA_KEYS_KEY, extra_keys)
        self._wrapped.handle(record)

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        # Wraps other calls to real handler
        return getattr(self._wrapped, attr)
