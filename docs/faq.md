# FAQ

## Why a new library and why not using [structlog](https://www.structlog.org)?

[structlog](https://www.structlog.org) is a "non standard" library (with some kind of non-perfect adapters with the standard logging system)
designed before {{contextvars}}.

It's clearly a very clever piece of code but we prefer to keep around the {{pythonlogging}}.

## Dependency free? Why?

Because log library are ubiquitous and to avoid any dependency conflicts, `stlog` was built to have **no dependency at all** but:

- borrows plenty of ideas and code from [daiquiri](https://github.com/Mergifyio/daiquiri) library (thanks to [Mergify](https://mergify.com/) and [Julien DANJOU](https://julien.danjou.info/).
- borrows some code from [python-json-logger](https://github.com/madzak/python-json-logger) (thanks to [Zakaria ZAJAC](https://github.com/madzak))
- borrows some ode from [python-logmter](https://github.com/jteppinette/python-logfmter) (thanks to [Joshua Taylor Eppinette](https://github.com/jteppinette))
- can use fancy stuff (colors, augmented traceback...) from the {{rich}} *(only if installed)*

This is an opinionated choice. But we assume that.
