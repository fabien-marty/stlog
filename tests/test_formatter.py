from __future__ import annotations

import json
import logging

import pytest

from stlog.base import STLOG_EXTRA_KEY
from stlog.formatter import (
    DEFAULT_STLOG_DATE_FORMAT,
    DEFAULT_STLOG_HUMAN_FORMAT,
    DEFAULT_STLOG_LOGFMT_FORMAT,
    HumanFormatter,
    JsonFormatter,
    LogFmtFormatter,
)


@pytest.fixture
def log_record() -> logging.LogRecord:
    record = logging.LogRecord(
        name="name",
        level=logging.INFO,
        pathname="/foo.py",
        lineno=1,
        msg="foo %s bar %s",
        args=("foo", "bar"),
        exc_info=None,
        func=None,
        sinfo=None,
    )
    record.foo = "bar"
    record.foo2 = "bar2"
    setattr(record, STLOG_EXTRA_KEY, ["foo", "foo2"])
    return record


@pytest.fixture
def human_formatter() -> logging.Formatter:
    return HumanFormatter(
        fmt=DEFAULT_STLOG_HUMAN_FORMAT, datefmt=DEFAULT_STLOG_DATE_FORMAT
    )


@pytest.fixture
def json_formatter() -> logging.Formatter:
    return JsonFormatter()


@pytest.fixture
def logfmt_formatter() -> logging.Formatter:
    return LogFmtFormatter(
        fmt=DEFAULT_STLOG_LOGFMT_FORMAT, datefmt=DEFAULT_STLOG_DATE_FORMAT
    )


def test_human1(log_record, human_formatter):
    res = human_formatter.format(log_record)
    assert res.startswith("2023")
    assert "INFO" in res
    assert "name" in res
    assert "foo foo bar bar" in res


def test_human2(log_record, human_formatter):
    setattr(log_record, STLOG_EXTRA_KEY, ("key1", "key2", "_key3"))
    log_record.key1 = "value1"
    log_record.key2 = 123
    log_record._key3 = 456
    res = human_formatter.format(log_record)
    assert "key1=value1" in res
    assert "key2=123" in res
    assert "_key3=456" not in res


def test_truncate_keys(log_record):
    setattr(log_record, STLOG_EXTRA_KEY, ("abcdefghijk", "abc"))
    log_record.abc = "value1"
    log_record.abcdefghijk = "value2"
    human_formatter = HumanFormatter(
        fmt=DEFAULT_STLOG_HUMAN_FORMAT,
        datefmt=DEFAULT_STLOG_DATE_FORMAT,
        extra_key_max_length=5,
    )
    res = human_formatter.format(log_record)
    assert "abc=value1" in res
    assert "ab...=value2" in res


def test_json1(log_record, json_formatter):
    res = json.loads(json_formatter.format(log_record))
    print(res)
    assert res["logger"] == log_record.name
    assert res["source"]["path"] == log_record.pathname
    assert str(res["source"]["lineno"]) == str(log_record.lineno)
    assert res["level"] == "INFO"
    assert res["time"].startswith("2023")
    assert res["message"] == "foo foo bar bar"


def test_json2(log_record):
    json_formatter = JsonFormatter(include_extras_in_key=None)
    res = json.loads(json_formatter.format(log_record))
    print(res)
    assert res["logger"] == log_record.name
    assert res["source"]["path"] == log_record.pathname
    assert str(res["source"]["lineno"]) == str(log_record.lineno)
    assert res["level"] == "INFO"
    assert res["time"].startswith("2023")
    assert res["message"] == "foo foo bar bar"


def test_logfmt(log_record, logfmt_formatter):
    res = logfmt_formatter.format(log_record)
    assert (
        res
        == 'time=2023-03-29T14:48:37Z logger=name level=INFO message="foo foo bar bar" foo=bar foo2=bar2'
    )
