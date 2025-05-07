from __future__ import annotations

import logging
from io import StringIO
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


def test_custom_rich_handler():
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    output = StringIO()
    h = CustomRichHandler(stream=output, force_terminal=True)
    h.emit(record)
    assert (
        output.getvalue().encode("utf-8")
        == b"\xe2\x96\xb6 \x1b[2;36m2023-03-29T14:48:37Z\x1b[0m test \x1b[34m  INFO  \x1b[0m \x1b[1mTest message\x1b[0m\n"
    )
