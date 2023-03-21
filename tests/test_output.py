from __future__ import annotations

from logging import StreamHandler

from stlog.formatter import (
    DEFAULT_STLOG_HUMAN_FORMAT,
    HumanFormatter,
)
from stlog.handler import CustomRichHandler
from stlog.output import (
    RichStreamOutput,
    StreamOutput,
    make_stream_or_rich_stream_output,
)


def test_automatic_rich():
    x = make_stream_or_rich_stream_output(use_rich=None)
    assert not isinstance(x, RichStreamOutput)
    assert isinstance(x, StreamOutput)
    assert isinstance(x.get_handler(), StreamHandler)
    assert isinstance(x.formatter, HumanFormatter)
    assert x.formatter.fmt == DEFAULT_STLOG_HUMAN_FORMAT
    y = make_stream_or_rich_stream_output(use_rich=True)
    assert isinstance(y, RichStreamOutput)
    assert isinstance(y.get_handler(), CustomRichHandler)
