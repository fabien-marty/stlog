from __future__ import annotations

import json
import logging

import pytest

from stlog import setup
from stlog.context import ExecutionLogContext
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
    standard_logger = logging.getLogger("standard")
    standard_logger.info("this is a test")
    assert len(target_list) == 1
    assert json.loads(target_list[0])["foo"] == "bar"
