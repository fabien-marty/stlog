from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any

_LOGGING_CONTEXT_VAR: ContextVar = ContextVar("stlog_logging_context", default={})


class ExecutionContext:
    @classmethod
    def reset_context(cls) -> None:
        _LOGGING_CONTEXT_VAR.set({})

    @classmethod
    def _add(cls, **kwargs) -> Token:
        new_context = _LOGGING_CONTEXT_VAR.get()
        # we create a new dict here as set() does a shallow copy
        return _LOGGING_CONTEXT_VAR.set({**new_context, **kwargs})

    @classmethod
    def add(cls, **kwargs) -> None:
        """Add some key / values to the execution context.

        WARNING: use only immutable values in kwargs (or be sure to never change them after add() call)
        """
        cls._add(**kwargs)

    @classmethod
    def remove(cls, *keys) -> None:
        # we create a new dict here as set() does a shallow copy
        _LOGGING_CONTEXT_VAR.set(
            {k: v for k, v in _LOGGING_CONTEXT_VAR.get().items() if k not in keys}
        )

    @classmethod
    def _get(cls) -> dict[str, Any]:
        # warning: do not modify the result dict
        return _LOGGING_CONTEXT_VAR.get()

    @classmethod
    @contextmanager
    def bind(cls, **kwargs):
        try:
            token = cls._add(**kwargs)
            yield
        finally:
            _LOGGING_CONTEXT_VAR.reset(token)
