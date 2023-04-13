from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any, Mapping

_LOGGING_CONTEXT_VAR: ContextVar = ContextVar("stlog_logging_context", default={})


class ExecutionLogContext:
    """This is a static class which hosts some utility (static) methods around a "log context" (global but by execution (worker/thread/async) thanks to contextvars)."""

    def __new__(cls):
        raise TypeError("This is a static class: do not instanciate it")

    @classmethod
    def reset_context(cls) -> None:
        """Reset the execution log context."""
        _LOGGING_CONTEXT_VAR.set({})

    @classmethod
    def _add(cls, **kwargs: Any) -> Token:
        new_context = _LOGGING_CONTEXT_VAR.get()
        # we create a new dict here as set() does a shallow copy
        return _LOGGING_CONTEXT_VAR.set({**new_context, **kwargs})

    @classmethod
    def add(cls, **kwargs: Any) -> None:
        """Add some key / values to the execution context.

        WARNING: use only immutable values in kwargs (or be sure to never change them after add() call)
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
        """Get the context as a dict.

        WARNING: this is a "private" method and be sure to never modify the result dict.
        """
        return _LOGGING_CONTEXT_VAR.get()

    @classmethod
    @contextmanager
    def bind(cls, **kwargs: Any):
        """Temporary bind some key / values to the execution log context (context manager).

        WARNING: use only immutable values in kwargs (or be sure to never change them after bind() call)

        """
        try:
            token = cls._add(**kwargs)
            yield
        finally:
            _LOGGING_CONTEXT_VAR.reset(token)
