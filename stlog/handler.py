from __future__ import annotations

import logging

from stlog.base import (
    STLOG_EXTRA_KEY,
)
from stlog.context import ExecutionLogContext


class ContextReinjectHandlerWrapper(logging.Handler):
    def __init__(self, *, wrapped: logging.Handler):
        self._wrapped = wrapped

    def handle(self, record):
        if not hasattr(record, STLOG_EXTRA_KEY):
            # the context is not already injected in record
            # (this log didn't pass by stlog ContextVarsAdapter)
            # => let's fix that
            new_kwargs = ExecutionLogContext._get()
            extra_keys: set[str] = getattr(record, STLOG_EXTRA_KEY, set())
            for k, v in new_kwargs.items():
                setattr(record, k, v)
                extra_keys.add(k)
            setattr(record, STLOG_EXTRA_KEY, extra_keys)
        self._wrapped.handle(record)

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return getattr(self, attr)
        # Wraps other calls to real handler
        return getattr(self._wrapped, attr)
