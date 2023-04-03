from __future__ import annotations

import pytest

from stlog.base import GLOBAL_LOGGING_CONFIG


@pytest.fixture(scope="session", autouse=True)
def session_run_at_beginning(request):
    GLOBAL_LOGGING_CONFIG._unit_tests_mode = True

    def session_run_at_end():
        GLOBAL_LOGGING_CONFIG._unit_tests_mode = False

    request.addfinalizer(session_run_at_end)
