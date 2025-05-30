from __future__ import annotations

import json
import logging
import os
import tempfile
import warnings
from io import StringIO

import pytest

from stlog import LogContext, getLogger, setup
from stlog.formatter import JsonFormatter
from stlog.output import FileOutput, RichStreamOutput
from stlog.setup import (
    _logging_excepthook,
    critical,
    debug,
    error,
    exception,
    fatal,
    info,
    warn,
    warning,
)
from tests.utils import UnitsTestsJsonOutput, UnitsTestsOutput


@pytest.fixture
def context():
    context = LogContext
    context.reset_context()
    yield context
    context.reset_context()


def test_multiple_contexts(context):
    context.add(at_context_level="foo1")
    logger = getLogger("foo", at_logger_level="foo2")
    target_list: list[str] = []
    setup(
        outputs=[UnitsTestsOutput(target_list=target_list, formatter=JsonFormatter())]
    )
    logger.info("message %s", "foo", at_info_level="foo3")
    assert len(target_list) == 1
    decoded = json.loads(target_list[0])
    assert decoded["message"] == "message foo"
    assert decoded["at_context_level"] == "foo1"
    assert decoded["at_logger_level"] == "foo2"
    assert decoded["at_info_level"] == "foo3"


def test_rich_handler(context):
    context.add(at_context_level="foo1")
    logger = getLogger("foo", at_logger_level="foo2")
    stream = StringIO()
    output = RichStreamOutput(stream=stream, force_terminal=True)
    setup(outputs=[output])
    logger.info("message %s", "foo", at_info_level="foo3")
    assert (
        stream.getvalue().encode("utf-8")
        == b"\xe2\x96\xb6 \x1b[2;36m2023-03-29T14:48:37Z\x1b[0m foo \x1b[34m  INFO  \x1b[0m \x1b[1mmessage foo\x1b[0m\n    \xe2\x86\xaa \x1b[33mat_context_level\x1b[0m\x1b[1m=\x1b[0m\x1b[35mfoo1\x1b[0m \x1b[33mat_info_level\x1b[0m\x1b[1m=\x1b[0m\x1b[35mfoo3\x1b[0m \x1b[33mat_logger_level\x1b[0m\x1b[1m=\x1b[0m\x1b[35mfoo2\x1b[0m\n"
    )


def test_levels_setup(context):
    target_list: list[str] = []
    setup(
        level="WARNING",
        outputs=[UnitsTestsOutput(target_list=target_list, formatter=JsonFormatter())],
        extra_levels={"bar": "DEBUG"},
    )
    getLogger("foo").info("ignored")
    getLogger("bar").debug("not ignored")
    assert len(target_list) == 1
    decoded = json.loads(target_list[0])
    assert decoded["message"] == "not ignored"


def test_levels_output(context):
    target_list: list[str] = []
    setup(
        level="INFO",
        outputs=[
            UnitsTestsOutput(
                target_list=target_list, formatter=JsonFormatter(), level="WARNING"
            )
        ],
    )
    getLogger("bar2").info("ignored")
    assert len(target_list) == 0


def test_warnings():
    target_list: list[str] = []
    setup(
        capture_warnings=True,
        outputs=[
            UnitsTestsOutput(
                target_list=target_list, formatter=JsonFormatter(), level="WARNING"
            )
        ],
    )
    warnings.warn("this is a warning", DeprecationWarning, stacklevel=2)
    assert len(target_list) == 1
    decoded = json.loads(target_list[0])
    assert decoded["level"] == "WARNING"
    assert decoded["logger"] == "py.warnings"
    assert "this is a warning" in decoded["message"]


def test_exceptions():
    target_list: list[dict] = []
    setup(
        outputs=[UnitsTestsJsonOutput(target_list=target_list)],
    )
    try:
        raise Exception("foo")
    except Exception:
        getLogger("bar").critical("exception catched", exc_info=True)
    assert len(target_list) == 1
    assert target_list[0]["level"] == "CRITICAL"
    assert target_list[0]["message"] == "exception catched"
    assert "Traceback" in target_list[0]["exc_info"]


def test_exceptions2():
    target_list: list[dict] = []
    setup(
        logging_excepthook=None,
        outputs=[UnitsTestsJsonOutput(target_list=target_list)],
    )
    try:
        raise Exception("foo")
    except Exception as e:
        _logging_excepthook(Exception, e)
    assert len(target_list) == 1
    assert target_list[0]["level"] == "ERROR"


def test_filters():
    # filters at logger level
    def _filter(log_record: logging.LogRecord) -> bool:
        if log_record.getMessage() == "message to filter":
            return False
        return True

    target_list: list[dict] = []
    setup(
        outputs=[UnitsTestsJsonOutput(target_list=target_list)],
    )
    logger = getLogger("foo")
    logger.addFilter(_filter)
    logger.info("foo")
    logger.info("message to filter")
    assert len(target_list) == 1
    assert target_list[0]["message"] == "foo"
    logger.removeFilter(_filter)
    logger.info("foo")
    logger.info("message to filter")
    assert len(target_list) == 3


def test_filters2():
    # filters at handler/output level
    def _filter(log_record: logging.LogRecord) -> bool:
        if log_record.getMessage() == "message to filter":
            return False
        return True

    target_list: list[dict] = []
    setup(
        outputs=[UnitsTestsJsonOutput(target_list=target_list, filters=[_filter])],
    )
    logger = getLogger("foo")
    logger.info("foo")
    logger.info("message to filter")
    assert len(target_list) == 1
    assert target_list[0]["message"] == "foo"


def test_root_logger():
    target_list: list[dict] = []
    setup(outputs=[UnitsTestsJsonOutput(target_list=target_list)], level="DEBUG")
    debug("debug")
    info("info")
    warning("warning")
    warn("warn")
    error("error")
    critical("critical")
    fatal("fatal")
    try:
        raise Exception("foo")
    except Exception:
        exception("exception")
    import json

    print(json.dumps(target_list, indent=4))
    for msg, level in (
        ("debug", "debug"),
        ("info", "info"),
        ("warning", "warning"),
        ("warn", "warning"),
        ("error", "error"),
        ("critical", "critical"),
        ("fatal", "critical"),
        ("exception", "error"),
    ):
        d = next(x for x in target_list if x["message"] == msg)
        assert d["level"] == level.upper()
        if msg == "warn":
            d = next(x for x in target_list if x["logger"] == "py.warnings")
            assert "function is deprecated" in d["message"]
        if msg == "exception":
            assert "Traceback" in d["exc_info"]


def test_file_output():
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = os.path.join(tmpdir, "test.log")
        setup(outputs=[FileOutput(filename=filename)], level="DEBUG")
        info("info")
        with open(filename) as f:
            assert f.read() == "2023-03-29T14:48:37Z root [   INFO   ] info\n"
