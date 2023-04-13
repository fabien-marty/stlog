from __future__ import annotations

import logging
import typing

from daiquiri import setup as daiquiri_setup

from standard_structlog.output import STDERR, OutputInterface


def setup(
    *,
    level: int = logging.WARNING,
    outputs: typing.Iterable[OutputInterface] = [STDERR],
    program_name: str | None = None,
    capture_warnings: bool = True,
    set_excepthook: bool = True,
    extra_levels: typing.Iterable[tuple[str, str | int]] = [],
) -> None:
    """Set up Python logging.

    This sets up basic handlers for Python logging.

    :param level: Root log level.
    :param outputs: Iterable of outputs to log to.
    :param program_name: The name of the program. Auto-detected if not set.
    :param capture_warnings: Capture warnings from the `warnings` module.
    """
    daiquiri_setup(
        level=level,
        outputs=outputs,  # type: ignore
        program_name=program_name,
        capture_warnings=capture_warnings,
        set_excepthook=set_excepthook,
    )
    for lgger, lvel in extra_levels:
        if isinstance(lvel, str):
            lvel = lvel.upper()
        logging.getLogger(lgger).setLevel(lvel)
