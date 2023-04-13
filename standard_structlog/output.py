from __future__ import annotations

import logging
import sys
from abc import ABC, abstractmethod

from daiquiri.output import Datadog as DaiquiriDatadog
from daiquiri.output import File as DaiquiriFile
from daiquiri.output import Journal as DaiquiriJournal
from daiquiri.output import RotatingFile as DaiquiriRotatingFile
from daiquiri.output import Stream as DaiquiriStream
from daiquiri.output import Syslog as DaiquiriSyslog
from daiquiri.output import TimedRotatingFile as DaiquiriTimedRotatingFile

from standard_structlog.handler import (
    ContextReinjectHandlerWrapper,
)


class OutputInterface(ABC):
    @abstractmethod
    def add_to_logger(self, logger: logging.Logger) -> None:
        pass


class WrappedHandlerOutputMixin(OutputInterface):
    def add_to_logger(self, logger: logging.Logger) -> None:
        """Add this output to a logger."""
        logger.addHandler(ContextReinjectHandlerWrapper(self.handler))  # type: ignore


class Stream(WrappedHandlerOutputMixin, DaiquiriStream):
    pass


class File(WrappedHandlerOutputMixin, DaiquiriFile):
    pass


class RotatingFile(WrappedHandlerOutputMixin, DaiquiriRotatingFile):
    pass


class TimedRotatingFile(WrappedHandlerOutputMixin, DaiquiriTimedRotatingFile):
    pass


class Journal(WrappedHandlerOutputMixin, DaiquiriJournal):
    pass


class Syslog(WrappedHandlerOutputMixin, DaiquiriSyslog):
    pass


class Datadog(WrappedHandlerOutputMixin, DaiquiriDatadog):
    pass


STDERR: OutputInterface = Stream()
STDOUT: OutputInterface = Stream(sys.stdout)
