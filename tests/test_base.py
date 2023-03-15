from __future__ import annotations

import pytest

from stlog.base import StLogError, check_json_types_or_raise


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
