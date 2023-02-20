from __future__ import annotations

import collections
import logging
import typing

import daiquiri

from standard_structlog.context import ExecutionContext


class ContextVarsAdapter(daiquiri.KeywordArgumentAdapter):
    def process(
        self, msg: typing.Any, kwargs: collections.abc.MutableMapping[str, typing.Any]
    ) -> tuple[typing.Any, collections.abc.MutableMapping[str, typing.Any]]:
        new_kwargs = {**ExecutionContext._get(), **kwargs}
        return super().process(msg, new_kwargs)


def getLogger(name: str | None = None, **kwargs) -> ContextVarsAdapter:  # noqa: N802
    return ContextVarsAdapter(logging.getLogger(name), kwargs)
