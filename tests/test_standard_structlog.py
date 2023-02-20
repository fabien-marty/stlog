from __future__ import annotations

import pytest

import standard_structlog


@pytest.fixture
def logger():
    return standard_structlog.getLogger("tests")


class LogComparator(dict):
    def __ge__(self, other: dict):
        for key, value in other.items():
            try:
                if self[key] != value:
                    return False
            except KeyError:
                return False
        return True


@pytest.fixture()
def logs(caplog):
    caplog.set_level("DEBUG")

    def _logs():
        return [LogComparator(vars(record)) for record in caplog.records]

    return _logs


def test_log(logger, logs):
    logger.info("It works", foo="bar", x=123)

    assert logs() >= [{"message": "It works", "foo": "bar", "x": 123}]


def test_bind(logger):
    logger.bind(bar="foo")
    logger.bind(y=456)


# # {"message": "It works", "bar": "foo", "y": 456, "foo": "bar", "x": 123, "timestamp": "2023-02-18T12:35:50.184540+00:00", "status": "info", "logger": {"name": "__main__"}}

# with logger.bind(bar="wooooo"):
#     logger.info("It works (bound)", foo="bar", x=123)
#     # {"message": "It works (bound)", "bar": "wooooo", "y": 456, "foo": "bar", "x": 123, "timestamp": "2023-02-18T12:35:50.184698+00:00", "status": "info", "logger": {"name": "__main__"}}

# logger.info("It works again", foo="bar", x=123)
# # {"message": "It works again", "bar": "foo", "y": 456, "foo": "bar", "x": 123, "timestamp": "2023-02-18T12:35:50.184772+00:00", "status": "info", "logger": {"name": "__main__"}}

# # to check that the context is not linked to the original logger
# logger2 = getLogger("foo")
# logger2.info("plop")
# # {"message": "plop", "bar": "foo", "y": 456, "timestamp": "2023-02-18T12:37:21.951642+00:00", "status": "info", "logger": {"name": "foo"}}
