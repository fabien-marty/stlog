import sys
from stlog import setup, getLogger
from stlog.output import StreamOutput
from stlog.formatter import HumanFormatter

format = "{asctime} {levelname} from process #{process}: {message}\n    => {extras}"
asctime_format = "%H:%M:%SZ"
setup(
    outputs=[
        StreamOutput(
            stream=sys.stderr,
            formatter=HumanFormatter(fmt=format, datefmt=asctime_format),
        )
    ]
)

getLogger(__name__).warning("this is a warning", foo="bar", foo2="bar2")
