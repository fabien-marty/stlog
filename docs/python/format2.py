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
                    extras_template="{0} => {1}",
                    extras_separator=", ",
                    extras_prefix="\n    ",
                ),
            ),
        )
    ]
)

getLogger().warning("this is a warning", foo="bar", foo2="bar2")
