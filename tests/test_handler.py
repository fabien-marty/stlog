from __future__ import annotations

import json
import logging

import pytest

from stlog import setup
from stlog.context import LogContext
from stlog.formatter import JsonFormatter
from tests.utils import UnitsTestsOutput


@pytest.fixture
def context():
    context = LogContext
    context.reset_context()
    yield context
    context.reset_context()


def test_reinject_handler(context):
    target_list: list[str] = []
    setup(
        outputs=[UnitsTestsOutput(target_list=target_list, formatter=JsonFormatter())],
        read_extra_kwargs_from_standard_logging=True,
    )
    context.add(foo="bar")
    standard_logger = logging.getLogger("standard")
    standard_logger.info("this is a test", extra={"bar": "foo"})
    assert len(target_list) == 1
    assert json.loads(target_list[0])["foo"] == "bar"
    assert json.loads(target_list[0])["bar"] == "foo"
