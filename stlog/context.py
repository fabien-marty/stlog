from __future__ import annotations

import copy
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any, Mapping

from stlog.base import (
    RESERVED_ATTRS,
    StlogError,
    check_json_types_or_raise,
    get_env_context,
)

ENV_CONTEXT = get_env_context()
_LOGGING_CONTEXT_VAR: ContextVar = ContextVar(
    "stlog_logging_context", default=ENV_CONTEXT
)


class LogContext:
    """This is a static class which hosts some utility (static) methods around a "log context"
    (global but by execution (worker/thread/async) thanks to contextvars).

    All values are (deeply) copied to avoid any changes after adding them to the context.
    """

    def __new__(cls):
        raise TypeError("This is a static class: do not instanciate it")

    @classmethod
    def reset_context(cls) -> None:
        """Reset the execution log context."""
        _LOGGING_CONTEXT_VAR.set(ENV_CONTEXT)

    @classmethod
    def _add(cls, **kwargs: Any) -> Token:
        for key in kwargs.keys():
            if key in RESERVED_ATTRS:
                raise StlogError(f"key: {key} is not allowed (reserved key)")
        for val in kwargs.values():
            check_json_types_or_raise(val)
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
    def getall(cls) -> dict:
        """Get the full context as dict."""
        return copy.deepcopy(_LOGGING_CONTEXT_VAR.get())

    @classmethod
    @contextmanager
    def bind(cls, **kwargs: Any):
        """Temporary bind some key / values to the execution log context (context manager)."""
        try:
            token = cls._add(**kwargs)
            yield
        finally:
            _LOGGING_CONTEXT_VAR.reset(token)
