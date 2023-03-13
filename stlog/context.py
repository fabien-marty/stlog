from __future__ import annotations

import copy
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any, Mapping

from stlog.base import RESERVED_ATTRS, StLogError

_LOGGING_CONTEXT_VAR: ContextVar = ContextVar("stlog_logging_context", default={})


def _check_json_type_or_raise(to_check: Any):
    if to_check is None:
        return
    if not isinstance(to_check, (dict, list, bool, str, int, float, bool)):
        raise StLogError(
            "to_check should be a dict/list/bool/str/int/float/bool/None, found %s"
            % type(to_check)
        )
    if isinstance(to_check, list):
        for item in to_check:
            _check_json_type_or_raise(item)
    elif isinstance(to_check, dict):
        for key, value in to_check.items():
            if not isinstance(key, str):
                raise StLogError("dict keys should be str, found %s" % type(key))
            _check_json_type_or_raise(value)


class ExecutionLogContext:
    """This is a static class which hosts some utility (static) methods around a "log context"
    (global but by execution (worker/thread/async) thanks to contextvars).

    All values are (deeply) copied to avoid any changes after adding them to the context.
    """

    def __new__(cls):
        raise TypeError("This is a static class: do not instanciate it")

    @classmethod
    def reset_context(cls) -> None:
        """Reset the execution log context."""
        _LOGGING_CONTEXT_VAR.set({})

    @classmethod
    def _add(cls, **kwargs: Any) -> Token:
        for key in kwargs.keys():
            if key in RESERVED_ATTRS:
                raise StLogError("key: %s is not allowed (reserved key)" % key)
        for val in kwargs.values():
            _check_json_type_or_raise(val)
        new_context = _LOGGING_CONTEXT_VAR.get()
        # we create a new dict here as set() does a shallow copy
        return _LOGGING_CONTEXT_VAR.set(copy.deepcopy({**new_context, **kwargs}))

    @classmethod
    def add(cls, **kwargs: Any) -> None:
        """Add some key / values to the execution context.

        Only dict, list, int, str, float, bool and None types are allowed
        (or composition of these types).
        """
        cls._add(**kwargs)

    @classmethod
    def remove(cls, *keys: str) -> None:
        """Remove given keys from the context."""
        # we create a new dict here as set() does a shallow copy
        _LOGGING_CONTEXT_VAR.set(
            {k: v for k, v in _LOGGING_CONTEXT_VAR.get().items() if k not in keys}
        )

    @classmethod
    def _get(cls) -> Mapping[str, Any]:
        """Get the whole context as a dict."""
        return copy.deepcopy(_LOGGING_CONTEXT_VAR.get())

    @classmethod
    def get(cls, key: str, default=None) -> Any:
        """Get a context key."""
        return copy.deepcopy(_LOGGING_CONTEXT_VAR.get().get(key, default))

    @classmethod
    @contextmanager
    def bind(cls, **kwargs: Any):
        """Temporary bind some key / values to the execution log context (context manager)."""
        try:
            token = cls._add(**kwargs)
            yield
        finally:
            _LOGGING_CONTEXT_VAR.reset(token)
