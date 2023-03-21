from __future__ import annotations

import pytest

from stlog.base import (
    StLogError,
    check_json_types_or_raise,
    logfmt_format,
    logfmt_format_string,
    logfmt_format_value,
)


def test_check_json_types_or_raise():
    check_json_types_or_raise(None)
    check_json_types_or_raise("foo")
    check_json_types_or_raise([{"foo": 123, "bar": 456}, None, [1, 2, 3]])
    with pytest.raises(StLogError):
        # invalid type
        check_json_types_or_raise(set())
    with pytest.raises(StLogError):
        # non str dict keys
        check_json_types_or_raise({456: 123, "bar": 456})


def test_logfmt_format_string():
    assert logfmt_format_string("foo") == "foo"
    assert logfmt_format_string("foo foo") == '"foo foo"'
    assert logfmt_format_string("foo\nfoo") == "foo\\nfoo"
    assert logfmt_format_string("") == '""'


def test_logfmt_format_value():
    assert logfmt_format_value(False) == "false"
    assert logfmt_format_value(True) == "true"
    assert logfmt_format_value(None) == ""
    assert logfmt_format_value(1) == "1"
    assert logfmt_format_value("foo") == "foo"


def test_logfmt_format():
    test_dict = {"foo": "bar", "foo2": [1, 2, 3], "foo3": "bar3"}
    assert (
        logfmt_format(
            test_dict,
            ignore_compound_types=True,
        )
        == "foo=bar foo3=bar3"
    )
    assert (
        logfmt_format(
            test_dict,
            ignore_compound_types=False,
        )
        == 'foo=bar foo2="[1, 2, 3]" foo3=bar3'
    )
