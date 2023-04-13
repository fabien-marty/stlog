# FAQ

## Why a new library and why not using [structlog](https://www.structlog.org)?

[structlog](https://www.structlog.org) is a "non standard" library (with some kind of non-perfect adapters with the standard logging system).
It's clearly a very clever piece of code but we prefer to keep  FIXME


## Dependency free? Why?

The library has no dependency but:

- borrows plenty of ideas and code from [daiquiri](https://github.com/Mergifyio/daiquiri) library (thanks to [Mergify](https://mergify.com/) and [Julien DANJOU](https://julien.danjou.info/).
- borrows some code from [python-json-logger](https://github.com/madzak/python-json-logger) (thanks to [Zakaria ZAJAC](https://github.com/madzak))
- borrows some code from [python-logmter](https://github.com/jteppinette/python-logfmter) (thanks to [Joshua Taylor Eppinette](https://github.com/jteppinette))
- can use fancy stuff (colors, augmented traceback...) from the {{rich}} *(only if installed)*

FIXME