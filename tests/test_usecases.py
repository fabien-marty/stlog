from __future__ import annotations

import json

import pytest

from stlog import ExecutionLogContext, getLogger, setup
from stlog.formatter import JsonFormatter
from tests.utils import UnitsTestsOutput


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
