from __future__ import annotations

import contextvars
import datetime

import pytest

from stlog import LogContext
from stlog.base import StlogError


@pytest.fixture
def context():
    context = LogContext
    context.reset_context()
    yield context
    context.reset_context()


def test_basic(context):
    context.add(foo="bar")
    assert context.get("foo") == "bar"
    assert context._get().get("foo") == "bar"
    context.remove("foo")
    assert context.get("foo") is None
    with context.bind(foo="bar"):
        assert context.get("foo") == "bar"
    assert context.get("foo") is None


def test_bad_types(context):
    with pytest.raises(StlogError):
        context.add(foo=set())
    with pytest.raises(StlogError):
        context.add(foo=[{"foo", datetime.datetime.now()}])
    with pytest.raises(StlogError):
        context.add(foo={123: True})


def test_bad_keys(context):
    with pytest.raises(StlogError):
        context.add(filename="foo")


def test_deepcopy(context):
    v = [{"foo": "bar"}]
    context.add(foo=v)
    v[0]["foo"] = "foo"
    assert context.get("foo")[0]["foo"] == "bar"


def _test_another_context():
    LogContext.reset_context()
    LogContext.add(foo="foo")
    assert LogContext.get("foo") == "foo"


def test_multiple_context(context):
    context.add(foo="bar")
    assert context.get("foo") == "bar"
    contextvars.copy_context().run(_test_another_context)
    assert context.get("foo") == "bar"


def test_init():
    with pytest.raises(TypeError):
        LogContext()
