# Usage

## Setup

The first thing to do is to import and call the {{apilink("setup")}} function:

```python
from stlog import setup

# Set default configuration
setup()
```

You have to do this once, probably in your main code.
It will set up a new python logging configuration.

By default, we:

- set a default level of `INFO`
- set a human output on `stderr` (with an automatic choice between rich output (with colors...) and standard output depending if `rich` library is installed and if we write in a real terminal)

You can change these defaults with environment variables or with key/values in this {{apilink("setup")}} function.

## Get a logger

Then you can get a `stlog` logger. 

??? question "Why a custom logger? Can I use a standard python logging logger?"

    The `stlog` logger is a standard [LoggerAdapter](https://docs.python.org/3/library/logging.html#loggeradapter-objects). But you have to use it (and not a plain `logging.getLogger` one)
    to be able to pass extra context when you use your logger.

    If you don't need to pass extra context at logging time (because a global context is enough or because
    you don't want context at all), you can use a standard python logger.

```python
{{ code_example("usage1.py") }}
```

{{ code_example_to_svg("usage1.py") }}

## Set a context

You have 4 ways of defining some context. Let's describe them starting with the more general ones.

### (1) With environment variables  

#### First, you can use JSON inside `STLOG_JSON_CONTEXT` env var

```console
$ export STLOG_ENV_JSON_CONTEXT='{"foo": "bar", "foo2": 123}'
$ python <<EOF
{{ code_example("usage2.py") }}
EOF
```

{{ code_example_to_svg("usage2.sh", interpreter="bash") }}

#### Second, you can use `STLOG_CONTEXT_*` env var 

```console
$ export STLOG_ENV_CONTEXT_FOO="bar"
$ export STLOG_ENV_CONTEXT_FOO2="123"
$ python <<EOF
{{ code_example("usage2.py") }}
EOF
```

{{ code_example_to_svg("usage2bis.sh", interpreter="bash") }}

This is less hacky than the JSON way but:

- you don't control the case of keys
- you don't control the type of values (always `str`) *(can be an issue with JSON output)*

In both cases, env variables are only read once (at program startup).

You can completly disable this feature by setting `STLOG_IGNORE_ENV_CONTEXT=1`.

### (2) With `LogContext` static class

You can use the static class {{apilink("LogContext")}} where you want to define some key/values that will be copied
to each logger call context. 

In a web context for example, a common practice is to set some key/values in a middleware.

As this context is global 

```python
{{ code_example("usage3.py") }}
```

{{ code_example_to_svg("usage3.py") }}

??? question "`ExecutionGlobalContext` is global, what about using it in threads or in async code?"

    Thanks to {{contextvars}}, {{apilink("LogContext")}} is more clever than a global dict, it's a kind of global context but specific for each tread
    or for each coroutine.

    Here is a [good introduction](https://superfastpython.com/thread-context-variables-in-python/) about {{contextvars}}.

    You can considerer that {{ apilink("LogContext") }} is just a light wrapper on {{contextvars}}.


Note: you can also use the {{apilink("LogContext")}} class as a context manager

```python
{{ code_example("usage3bis.py") }}
```

{{ code_example_to_svg("usage3bis.py") }}

### (3) At the logger instantiation

```python
{{ code_example("usage4.py") }}
```

{{ code_example_to_svg("usage4.py") }}

### (4) At the logger log call

```python
{{ code_example("usage5.py") }}
```

{{ code_example_to_svg("usage5.py") }}

## Using the logger

The `stlog.Logger` is only an adapter on the [python standard Logger](https://docs.python.org/3/library/logging.html#logging.Logger).

So you can use it as a drop in replacement.

The only thing you get is the ability to pass some extra `kwargs` as key/values.

```python
{{ code_example("usage6.py") }}
```

{{ code_example_to_svg("usage6.py", lines=30) }}

## API reference

The public API of the library is available here: {{apilink()}}{:target="_blank"}.

!!! warning "Public API"

    Only what is documented on this previous link is considered as a part of the public API
    So, if it is not documented, it's a part of the private API (and it can change at any time).
