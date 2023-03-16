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


def test_reinject_handler(context):
    target_list: list[str] = []
    setup(
        outputs=[UnitsTestsOutput(target_list=target_list, formatter=JsonFormatter())]
    )
    context.add(foo="bar")
    logger = getLogger("standard", foo2="bar2")
    logger.info("this is a test", foo3="bar3")
    assert len(target_list) == 1
    assert json.loads(target_list[0])["foo"] == "bar"
    assert json.loads(target_list[0])["foo2"] == "bar2"
    assert json.loads(target_list[0])["foo3"] == "bar3"
