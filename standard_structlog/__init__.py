from __future__ import annotations

import collections
import logging
from contextvars import ContextVar
from typing import Any

import daiquiri

formatter = daiquiri.formatter
output = daiquiri.output

cvar: ContextVar[Any] = ContextVar("logger_context", default={})


class LogContextContextManager:
    def __init__(self, cvar: ContextVar[Any], **kwargs):
        self.cvar = cvar
        self.token = cvar.set({**cvar.get(), **kwargs})

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return self.unbind()

    def unbind(self):
        self.cvar.reset(self.token)


class ContextVarsAdapter(daiquiri.KeywordArgumentAdapter):
    def bind(self, **kwargs):
        return LogContextContextManager(cvar=cvar, **kwargs)

    def reset_context(self):
        cvar.set({})

    def process(
        self, msg: Any, kwargs: collections.abc.MutableMapping[str, Any]
    ) -> tuple[Any, collections.abc.MutableMapping[str, Any]]:
        new_kwargs = {**cvar.get(), **kwargs}
        return super().process(msg, new_kwargs)


def getLogger(name: str | None = None, **kwargs) -> ContextVarsAdapter:  # noqa: N802
    return ContextVarsAdapter(logging.getLogger(name), kwargs)


def setup(*args, **kwargs):
    daiquiri.setup(*args, **kwargs)
