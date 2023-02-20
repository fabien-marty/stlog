from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any

_LOGGING_CONTEXT_VAR: ContextVar = ContextVar("logger_context", default={})


class ExecutionContext:
    @classmethod
    def reset_context(cls) -> None:
        _LOGGING_CONTEXT_VAR.set({})

    @classmethod
    def _add(cls, **kwargs) -> Token:
        new_context = _LOGGING_CONTEXT_VAR.get()
        return _LOGGING_CONTEXT_VAR.set({**new_context, **kwargs})

    @classmethod
    def add(cls, **kwargs) -> None:
        cls._add(**kwargs)

    @classmethod
    def remove(cls, *keys) -> None:
        new_context = _LOGGING_CONTEXT_VAR.get()
        for key in keys:
            try:
                new_context.pop(key)
            except KeyError:
                pass
        _LOGGING_CONTEXT_VAR.set(new_context)

    @classmethod
    def get(cls) -> dict[str, Any]:
        return _LOGGING_CONTEXT_VAR.get()

    @classmethod
    @contextmanager
    def bind(cls, **kwargs):
        try:
            token = cls._add(**kwargs)
            yield
        finally:
            _LOGGING_CONTEXT_VAR.reset(token)
