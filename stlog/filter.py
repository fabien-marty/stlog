from __future__ import annotations

import logging

from stlog.base import RESERVED_ATTRS, STLOG_EXTRA_KEY
from stlog.context import LogContext


class ContextReinjectFilter(logging.Filter):
    """Logging Filter to reinject the global context in the log record.

    For example when the log record was emitted by a non stlog logger.

    The log record is modified in place and never filtered (filter() always
    return True).
    """

    def __init__(self, name="", read_extra_kwargs_from_standard_logging: bool = False):
        super().__init__(name)
        self.read_extra_kwargs_from_standard_logging = (
            read_extra_kwargs_from_standard_logging
        )

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, STLOG_EXTRA_KEY):
            # the context is not already injected in record
            # (this log didn't pass by stlog ContextVarsAdapter)
            # => let's fix that
            new_kwargs = LogContext._get()
            extra_keys: set[str] = getattr(record, STLOG_EXTRA_KEY, set())
            for k, v in new_kwargs.items():
                setattr(record, k, v)
                extra_keys.add(k)
            if self.read_extra_kwargs_from_standard_logging:
                # try to find special keys set by extra kwargs in
                # standard python logging
                for k in vars(record).keys():
                    if k not in RESERVED_ATTRS:
                        extra_keys.add(k)
            setattr(record, STLOG_EXTRA_KEY, extra_keys)
        return True
