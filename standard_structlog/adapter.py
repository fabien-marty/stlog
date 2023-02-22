from __future__ import annotations

import collections
import logging
import typing

import daiquiri

from standard_structlog.base import STLOG_MANAGED_KEY
from standard_structlog.context import ExecutionLogContext


class ContextVarsAdapter(daiquiri.KeywordArgumentAdapter):
    def process(
        self, msg: typing.Any, kwargs: collections.abc.MutableMapping[str, typing.Any]
    ) -> tuple[typing.Any, collections.abc.MutableMapping[str, typing.Any]]:
        new_kwargs = {**ExecutionLogContext._get(), **kwargs, STLOG_MANAGED_KEY: True}
        return super().process(msg, new_kwargs)


def getLogger(name: str | None = None, **kwargs) -> ContextVarsAdapter:  # noqa: N802
    return ContextVarsAdapter(logging.getLogger(name), kwargs)
