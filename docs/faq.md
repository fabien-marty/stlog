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

## Mixing `stlog` and python standard logging?

Not a problem!

```python
{{ code_example("usage_mix1.py") }}
```

{{ code_example_to_svg("usage_mix1.py") }}

Of course, when you use a classic python logger, you can't pass a specific context but the global context is automatically 
reinjected. If you don't want this behavior, set `reinject_context_in_standard_logging` to `False` in {{apilink("setup")}}:

```python
{{ code_example("usage_mix2.py") }}
```

{{ code_example_to_svg("usage_mix2.py") }}
