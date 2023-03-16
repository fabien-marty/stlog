from __future__ import annotations

from dataclasses import dataclass
from logging import StreamHandler

from rich.logging import RichHandler

from stlog.formatter import (
    DEFAULT_STLOG_HUMAN_FORMAT,
    DEFAULT_STLOG_RICH_FORMAT,
    HumanFormatter,
)
from stlog.output import Stream


@dataclass
class SpecialStream(Stream):
    force_resolve_rich: bool = False

    def _resolve_rich(self) -> None:
        self._use_rich = self.force_resolve_rich


def test_automatic_rich():
    x = Stream(use_rich=None)
    assert x._use_rich is False
    assert isinstance(x.get_handler(), StreamHandler)
    assert isinstance(x.formatter, HumanFormatter)
    assert x.formatter.fmt == DEFAULT_STLOG_HUMAN_FORMAT
    y = SpecialStream(force_resolve_rich=False)
    assert y._use_rich is False
    assert isinstance(y.get_handler(), StreamHandler)
    assert isinstance(y.formatter, HumanFormatter)
    assert y.formatter.fmt == DEFAULT_STLOG_HUMAN_FORMAT
    y = SpecialStream(force_resolve_rich=True)
    assert y._use_rich is True
    assert isinstance(y.get_handler(), RichHandler)
    assert isinstance(y.formatter, HumanFormatter)
    assert y.formatter.fmt == DEFAULT_STLOG_RICH_FORMAT
