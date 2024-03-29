import sys
from stlog import LogContext, getLogger, setup
from stlog.output import StreamOutput
from stlog.formatter import HumanFormatter, JsonFormatter

setup(
    outputs=[
        StreamOutput(
            stream=sys.stderr,
            formatter=HumanFormatter(exclude_extras_keys_fnmatchs=["*"]),
        ),
        StreamOutput(stream=sys.stdout, formatter=JsonFormatter(indent=4)),
    ]
)

# See previous example for details
LogContext.reset_context()
LogContext.add(request_id="4c2383f5")
LogContext.add(client_id=456, http_method="GET")
logger = getLogger(__name__)
logger.info("It works", foo="bar", x=123)
logger.critical("Houston, we have a problem!")
