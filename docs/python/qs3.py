import sys
from stlog import getLogger, setup
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

logger = getLogger(__name__)

# See previous example for details
logger.context.reset_context()
logger.context.add(request_id="4c2383f5")
logger.context.add(client_id=456, http_method="GET")
logger.info("It works", foo="bar", x=123)
logger.critical("Houston, we have a problem!")
