from __future__ import annotations

import json
import warnings
from unittest.mock import MagicMock

import pytest

from stlog import ExecutionLogContext, getLogger, setup
from stlog.formatter import JsonFormatter
from stlog.output import RichStreamOutput
from stlog.setup import _logging_excepthook
from tests.utils import UnitsTestsJsonOutput, UnitsTestsOutput


@pytest.fixture
def context():
    context = ExecutionLogContext
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
    output = RichStreamOutput(force_terminal=True)
    setup(outputs=[output])
    output.console.print = MagicMock(return_value=None)
    logger.info("message %s", "foo", at_info_level="foo3")
    output.console.print.assert_called_with(
        ":arrow_forward: [log.time]2023-03-29T14:48:37Z[/log.time] foo [logging.level.info]  INFO  [/logging.level.info] [bold]message foo[/bold]\n    :arrow_right_hook: [repr.attrib_name]at_context_level[/repr.attrib_name][repr.attrib_equal]=[/repr.attrib_equal][repr.attrib_value]foo1[/repr.attrib_value] [repr.attrib_name]at_info_level[/repr.attrib_name][repr.attrib_equal]=[/repr.attrib_equal][repr.attrib_value]foo3[/repr.attrib_value] [repr.attrib_name]at_logger_level[/repr.attrib_name][repr.attrib_equal]=[/repr.attrib_equal][repr.attrib_value]foo2[/repr.attrib_value]"
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
    warnings.warn("this is a warning", DeprecationWarning)
    assert len(target_list) == 1
    decoded = json.loads(target_list[0])
    assert decoded["status"] == "warning"
    assert decoded["logger"]["name"] == "py.warnings"
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
    assert target_list[0]["status"] == "critical"
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
    assert target_list[0]["status"] == "critical"
