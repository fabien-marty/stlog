import sys
from stlog import setup, getLogger
from stlog.output import StreamOutput
from stlog.formatter import HumanFormatter


setup(outputs=StreamOutput(stream=sys.stderr, formatter=HumanFormatter()))

getLogger(__name__).warning("this is a warning", foo="bar", foo2="bar2")
