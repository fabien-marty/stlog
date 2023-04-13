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

## `ExecutionGlobalContext` is global, what about using it in threads or in async code?

Thanks to {{contextvars}}, {{apilink("ExecutionLogContext")}} is more clever than a global dict, it's a kind of global context but specific for each tread
or for each coroutine.

Here is a [good introduction](https://superfastpython.com/thread-context-variables-in-python/) about {{contextvars}}.

You can considerer that {{ apilink("ExecutionLogContext") }} is just a light wrapper on {{contextvars}}.

## How to inject a global context from environment variables?

### First, you can use JSON inside `STLOG_JSON_CONTEXT` env var

```console
$ export STLOG_ENV_JSON_CONTEXT='{"foo": "bar", "foo2": 123}'
$ python <<EOF
from stlog import setup, getLogger

setup()
getLogger().info("this is a test")
EOF
2023-03-24T09:48:23Z [INFO]     (root) this is a test {foo="foo bar" foo2=123}
```

### Second, you can use `STLOG_CONTEXT_*` env var 

```console
$ export STLOG_ENV_CONTEXT_FOO="foo bar"
$ export STLOG_ENV_CONTEXT_FOO2="123"
$ python <<EOF
from stlog import setup, getLogger

setup()
getLogger().info("this is a test")
EOF
2023-03-24T09:48:23Z [INFO]     (root) this is a test {foo="foo bar" foo2=123}
```

This is less hacky than the JSON way but:

- you don't control the case of keys
- you don't control the type of values (always `str`) *(can be an issue with JSON output)*

In both cases, env variables are only read once (at program startup).

You can completly disable this feature by setting `STLOG_IGNORE_ENV_CONTEXT=1`.



