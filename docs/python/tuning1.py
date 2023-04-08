from stlog import setup
import logging

setup(read_extra_kwarg_from_standard_logging=True)
logging.warning(
    "standard logger with extra kwargs", extra={"foo": "bar", "foo2": "bar2"}
)
