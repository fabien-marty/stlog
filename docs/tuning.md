# Tuning

!!! notice "To go further..."
    This page is about tuning existing `stlog` objects. To go further, you can also read the [Extend](../extend) page.

## The `setup()` function

### The log level

First of all, you can tune the (minimal) log level as a global parameter for all outputs/loggers.

```python
from stlog import setup, getLogger

# Filter messages < WARNING
setup(level="WARNING") 
getLogger().info("ignored message")
```

You can also override this in the {{apilink("setup")}} function for a specific logger name:

```python
from stlog import setup, getLogger

# Filter messages < WARNING
setup(level="WARNING", extra_levels={"bar": "DEBUG"}) 
getLogger("foo").info("ignored message")
getLogger("bar").debug("not ignored message thanks to the extra_levels override")
```

Of course, you can still use `setLevel()` on logger instances.

!!! tip

    You can also use logging levels as integer. Example: `logging.DEBUG`

### The outputs

The main configuration option of the {{apilink("setup")}} function is the `outputs` parameter 
which takes a list of {{apilink("Output")}} objects.

You can see how to create your own outputs in the [extend page](../extend).

For now, you can use two kind of outputs:

- a {{apilink("output.StreamOutput")}} object which represents a standard stream output (for example on the console `stdout` or `stderr`)
- a {{apilink("output.RichStreamOutput")}} object which represents a "rich" stream output for a real and modern terminal emulator (with colors and fancy stuff)

!!! warning "rich library"

    To use a {{apilink("RichStreamOutput")}}, you must install {{rich}} by yourself. 
    It's a **mandatory requirement** for this ouput.

If you don't know which one to use or if you need an automatic behavior (depending on the fact that {{rich}} is installed or not
or if we are writing to a real terminal and not to a filter redirected to a file for example), you can use a very handy 
factory: {{apilink("output.make_stream_or_rich_stream_output")}} which will automatically choose for you.

Each `Output` can provide custom options but there are two common ones:

- `formatter` which can be used to override the default `logging.Formatter` object
- `level` which can be used to override the default logging level (for this specific output if this level is not already filtered at `Logger` level)
- `filters` which can be used to add some `logging.Filter` for this specific output *(note: you can also add filters at the logger level with `addFilter()` method)*

Here is an example to configure two outputs: 

- one classic stream output to `stderr` with an overridden formatter and an overridden log level
- one classic stream output to `stdout` with a JSON formatter

```python
import sys
from stlog import setup
from stlog.output import StreamOutput
from stlog.formatter import HumanFormatter, JsonFormatter

setup(
    level="INFO",
    outputs=[
        StreamOutput(
            stream=sys.stderr,
            formatter=HumanFormatter(exclude_extras_keys_fnmatchs=["*"]),
            level="WARNING",
        ),
        StreamOutput(stream=sys.stdout, formatter=JsonFormatter(indent=4)),
    ]
)
```

!!! question "Formatters?"

    You have a dedicated section about `Formatters` and `stlog` custom `Formatters` bellow.

Default output is and "automatic rich or not rich" stream on `stderr` with a `HumanFormatter` as formatter.

??? question "Filters?"

    Here is an example:

    ```python
    import sys
    import logging
    from stlog import setup, getLogger
    from stlog.output import StreamOutput
    from stlog.formatter import HumanFormatter, JsonFormatter

    def this_is_a_filter(record: logging.LogRecord) -> False:
        if record.getMessage() == "message to filter":
            # We don't want this message
            return False
        return True

    setup(
        level="INFO",
        outputs=[
            StreamOutput(
                stream=sys.stderr,
                formatter=HumanFormatter(exclude_extras_keys_fnmatchs=["*"]),
                level="WARNING",
            ),
            StreamOutput(stream=sys.stdout, formatter=JsonFormatter(indent=4)),
            filters=[this_is_a_filter],
        ]
    ) 
    
    getLogger("foo").info("message to filter") # this message will be filtered

    ```

### Warnings and "not catched" exceptions

[Python warnings](https://docs.python.org/3/library/warnings.html) are automatically captured with the `stlog` logging infrastructure.
You can disable this with `capture_warnings=False` parameter:

```python
from stlog import setup

setup(
    capture_warnings=False
)
```

Moreover, `stlog` capture your "not catched" exceptions to emit them as `ERROR` messages. You can disable this or tune this with:

```python
from stlog import setup

setup(
    logging_excepthook=None
)
```

You can also provide your own hook. See [this python documentation](https://docs.python.org/3/library/sys.html#sys.excepthook) for details.

### Standard logging compatibility options

By default, `stlog` is going to inject global contexts into standard logging calls.

If you want to disable this behavior:

```python
from stlog import setup

setup(
    reinject_context_in_standard_logging=False
)
```

You can go further by connecting the standard logging `extra` kwargs to `stlog`:

```python
{{ code_example("tuning1.py") }}
```

{{ code_example_to_svg("tuning1.py") }}

## Formatters

FIXME

## Available Environment variables

As we love {{twelvefactorapp}} plenty of default behavior of `stlog` can be configured with environment variables.

!!! note "configuration priority?"

    In order of importance (the last one wins):

    - default values (set in the code)
    - environment variables
    - explicit configuration in the code (always wins)

### `STLOG_USE_RICH``

This variable can tune the behavior of {{apilink("output.make_stream_or_rich_stream_output")}} function:

- if empty or set to `NONE`  or `AUTO` => nothing (the function makes automatically a `StreamOuput` or a `RichStreamOutput`, see above for details)
- if set to `1`, `TRUE`, `YES` => the function will always return a `RichStreamOutput` (even the log stream is redirected to a file!)
- else (`0`, `FALSE`, `NO`...) => the function will always return a standard `StreamOutput` (with colors and fancy things)

!!! question "`use_rich` parameter?"

    This can be overriden by the `use_rich` parameter when calling {{apilink("output.make_stream_or_rich_stream_output")}} 

### `STLOG_CAPTURE_WARNINGS`

This variable can change the default value of `capture_warnings` parameter of the {{apilink("setup")}} function: 

- if set to `0`, `FALSE`, `NO`: default value of `capture_warnings` is set to `False`

### `STLOG_REINJECT_CONTEXT_IN_STANDARD_LOGGING` 

This variable can change the default value of `reinject_context_in_standard_logging` parameter of the {{apilink("setup")}} function: 

- if set to `0`, `FALSE`, `NO`: default value of `reinject_context_in_standard_logging` is set to `False`

## `STLOG_READ_EXTRA_KWARGS_FROM_STANDARD_LOGGING`

This variable can change the default value of `read_extra_kwarg_from_standard_logging` parameter of the {{apilink("setup")}} function: 

- if set to `1`, `TRUE`, `YES`: default value of `read_extra_kwarg_from_standard_logging` is set to `True`

FIXME:

- STLOG_ENV_JSON_CONTEXT
- STLOG_ENV_CONTEXT_*
- STLOG_UNIT_TESTS_MODE
- STLOG_LOGFMT_IGNORE_COMPOUND_TYPES
- STLOG_PROGRAM_NAME