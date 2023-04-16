import sys
from stlog import setup, getLogger
from stlog.kvformatter import TemplateKVFormatter
from stlog.output import StreamOutput
from stlog.formatter import HumanFormatter


setup(
    outputs=[
        StreamOutput(
            stream=sys.stderr,
            formatter=HumanFormatter(
                fmt="{asctime}: ***{levelname}*** {message}{extras}",
                kv_formatter=TemplateKVFormatter(
                    template="{key} => {value}",
                    separator=", ",
                    prefix="\n    ",
                ),
            ),
        )
    ]
)

getLogger().warning("this is a warning", foo="bar", foo2="bar2")
