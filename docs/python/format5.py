import sys
from stlog import setup, getLogger
from stlog.output import StreamOutput
from stlog.formatter import LogFmtFormatter


fmt = "time={asctime} logger={name} process={process} level={levelname} message={message}{extras}"
setup(outputs=[StreamOutput(stream=sys.stderr, formatter=LogFmtFormatter(fmt=fmt))])

getLogger(__name__).warning("this is a warning", foo="bar", foo2="bar2")
getLogger(__name__).critical(
    'this is a critical message with\nmultiple\nlines and "quotes"'
)
