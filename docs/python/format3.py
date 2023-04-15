import sys
from stlog import setup, getLogger
from stlog.kvformatter import LogFmtKVFormatter
from stlog.output import StreamOutput
from stlog.formatter import HumanFormatter

setup(
    outputs=[
        StreamOutput(
            stream=sys.stderr,
            formatter=HumanFormatter(
                fmt="{asctime}: ***{levelname}*** {message}{extras}",
                kv_formatter=LogFmtKVFormatter(
                    extras_prefix=" [",
                    extras_suffix="]",
                ),
            ),
        )
    ]
)

getLogger().warning("this is a warning", foo="foo bar", foo2="bar2")
