from __future__ import annotations

import collections
import logging
import typing
from contextlib import contextmanager
from contextvars import ContextVar, Token

import daiquiri

formatter = daiquiri.formatter
output = daiquiri.output

cvar = ContextVar("logger_context", default={})


class ContextVarsAdapter(daiquiri.KeywordArgumentAdapter):
    def reset_context(self) -> Token:
        return cvar.set({})

    def add_to_context(self, **kwargs) -> Token:
        new_context = cvar.get()
        return cvar.set({**new_context, **kwargs})

    def remove_from_context(self, *keys: str) -> Token:
        new_context = self.cvar.get()
        for key in keys:
            new_context.pop(key)
        return cvar.set(new_context)

    @contextmanager
    def bind(self, **kwargs):
        try:
            token = self.add_to_context(**kwargs)
            yield
        finally:
            cvar.reset(token)

    def process(
        self, msg: typing.Any, kwargs: collections.abc.MutableMapping[str, typing.Any]
    ) -> tuple[typing.Any, collections.abc.MutableMapping[str, typing.Any]]:
        new_kwargs = {**cvar.get(), **kwargs}
        return super().process(msg, new_kwargs)


def getLogger(name: str | None = None, **kwargs) -> ContextVarsAdapter:  # noqa: N802
    return ContextVarsAdapter(logging.getLogger(name), kwargs)


def setup(*args, **kwargs):
    daiquiri.setup(*args, **kwargs)
