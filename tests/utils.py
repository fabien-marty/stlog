from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from stlog.formatter import JsonFormatter
from stlog.output import Output


class UnitsTestsHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        if "target_list" not in kwargs:
            raise Exception("target_list must be set in kwargs")
        self._target_list = kwargs.pop("target_list")
        super().__init__(*args, **kwargs)

    def emit(self, record):
        if self._target_list is None:
            return
        formatted = self.format(record)
        self._target_list.append(formatted)


class JsonUnittestsHandler(UnitsTestsHandler):
    def emit(self, record):
        if self._target_list is None:
            return
        formatted = self.format(record)
        self._target_list.append(json.loads(formatted))


@dataclass
class UnitsTestsOutput(Output):
    target_list: list | None = None

    def __post_init__(self):
        self.set_handler(UnitsTestsHandler(target_list=self.target_list))


@dataclass
class UnitsTestsJsonOutput(Output):
    target_list: list | None = None

    def __post_init__(self):
        self.formatter = JsonFormatter()
        self.set_handler(JsonUnittestsHandler(target_list=self.target_list))
