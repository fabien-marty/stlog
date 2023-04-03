from __future__ import annotations

import os
from unittest import mock

import pytest

from stlog.base import (
    StLogError,
    check_json_types_or_raise,
    check_true,
    get_env_context,
    logfmt_format,
    logfmt_format_string,
    logfmt_format_value,
    rich_logfmt_format,
    rich_markup_escape,
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


def test_rich_logfmt_format():
    test_dict = {"foo": "bar", "foo2": [1, 2, 3], "foo3": "bar3"}
    assert (
        rich_logfmt_format(
            test_dict,
            ignore_compound_types=True,
        )
        == "[repr.attrib_name]foo[/repr.attrib_name][repr.attrib_equal]=[/repr.attrib_equal][repr.attrib_value]bar[/repr.attrib_value] [repr.attrib_name]foo3[/repr.attrib_name][repr.attrib_equal]=[/repr.attrib_equal][repr.attrib_value]bar3[/repr.attrib_value]"
    )


@mock.patch.dict(os.environ, {"STLOG_ENV_JSON_CONTEXT": '{"foo": "bar", "foo2": 123}'})
def test_get_env_context_json():
    assert get_env_context() == {"foo": "bar", "foo2": 123}


@mock.patch.dict(os.environ, {"STLOG_ENV_JSON_CONTEXT": "{"})
def test_get_env_context_invalid_json():
    assert get_env_context() == {}


@mock.patch.dict(
    os.environ, {"STLOG_ENV_CONTEXT_FOO": "bar", "STLOG_ENV_CONTEXT_FOO2": "123"}
)
def test_get_env_context():
    assert get_env_context() == {"foo": "bar", "foo2": "123"}


@mock.patch.dict(
    os.environ,
    {"STLOG_ENV_CONTEXT_FOO": "bar", "STLOG_ENV_CONTEXT_": "123", "FOO": "BAR"},
)
def test_get_env_context2():
    assert get_env_context() == {"foo": "bar"}


def test_rich_markup_escape():
    assert rich_markup_escape("[foo]bar[/foo]") == "\\[foo]bar\\[/foo]"


def test_check_true():
    assert check_true(None) is False
    assert check_true("foo") is False
    assert check_true("True") is True
    assert check_true("yeS") is True
    assert check_true("1") is True
