# Configure

!!! notice "To go further..."
    This page is about configuring existing `stlog` objects. To go further, you can also read the [Extend](../extend) page.

## The `setup()` function

??? question "`stlog` library seems great but I don't want to use a special way to configure it!"

    Yes, you can configure `stlog` library without custom shortcuts like `Output` or `setup()`. See [FAQ](../faq) for details about that.

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
which takes a list of {{apilink("output.Output")}} objects.

You can see how to create your own outputs in the [extend page](../extend).

For now, you can use two kind of outputs:

- a {{apilink("output.StreamOutput")}} object which represents a standard stream output (for example on the console `stdout` or `stderr`)
- a {{apilink("output.RichStreamOutput")}} object which represents a "rich" stream output for a real and modern terminal emulator (with colors and fancy stuff)

!!! warning "rich library"

    To use a {{apilink("output.RichStreamOutput")}}, you must install {{rich}} by yourself. 
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
{{ code_example("configure1.py") }}
```

{{ code_example_to_svg("configure1.py") }}

## Formatters

In `stlog` we have two kinds of formatters:

- standard/classic formatters in `stlog.formatters`: they are compatible with [python logging Formatters](https://docs.python.org/3/library/logging.html#logging.Formatter)
- kvformatters in `stlog.kvformatters`: these custom classes build a new `extras` placeholder (with all key/values from contexts) you can use in your standard formatters (as a part on the format string)

## KV formatters

Let's start with "KV formatters". They are completely specific to `stlog` but optional. They format extra key values into a single `{extras}`
placeholder you can use classically with "standard formatters". They are optional because you can also use individual placeholders for each
key/value.

Let's say, you have to extra key values:

- `foo="bar"`
- `foo2="bar2"`

In the standard formatter format, you can use `{foo}` and `{foo2}` placeholders without a "KV formatter" at all. But you need to know the 
name of all key values you want to add to your log messages (because you have to list them in the format string):

Example: 

- if the formatter format string is `{levelname}: {message} (foo={foo}, foo2={foo2})"` and if you log with `stlog.getLogger().warning("this is a warning", foo="bar", foo2="bar2")`, you are going to get: `warning: this is a warning (foo=bar, foo2=bar2)`
- but if you use a `LogFmtKVFormatter` and a format string: `{levelname}: {message} {extras}`, you are going to get: `warning: this is a warning {foo=bar, foo2=bar2}`

So "KV formatters" are only responsible of serializing all extra key values to an `{extras}` string placeholder. If you don't use
this placeholder in your format string, you don't need a "KV formatter" at all.

!!! question "what about `%(extras)s` placeholder instead?"

    `stlog` use new formatter strings (with `style="{"`). So placeholders are using the form: `{name}`. If you prefer old-style
    placeholders with `style="%"` you can of course switch to the old-style and you use `%(extras)s` placeholder instead.

### Available "KV formatters"

Here are available "KV formatters". You can of course write yours (see [extend page in documentation](../extend)).

#### `EmptyKVFormatter`

This one is not very interesting as it always returns an empty string as `{extras}`.

#### `TemplateKVFormatter`

This one formats `{extras}` with string templating.

See {{apilink("kvformatter.TemplateKVFormatter")}} for details.

Example:

```python
{{ code_example("format2.py") }}
```

```
{{ code_example_to_output("format2.py") }}
```

#### `LogFmtKVFormatter`

This class formats `{extras}` with {{logfmt}}.

See {{apilink("kvformatter.LogFmtKVFormatter")}} for details.

Example:

```python
{{ code_example("format3.py") }}
```

```
{{ code_example_to_output("format3.py") }}
```

??? question "What about compound types in extras?"

    FIXME

## Standard formatters

### Common options

All `stlog` formatters have common options you can find on {{apilink("formatter.Formatter", title="the API reference")}}.

These options are common `logging.Formatter` options extended with some `stlog` custom options.

Extra options are mainly about context key/values formatting. We are going to see some real examples after.

### `HumanFormatter`

This formatter can be used to get a human friendly output (without {{rich}}).

Let's start with a simple example:

```python
{{ code_example("format1.py") }}
```

```
{{ code_example_to_output("format1.py") }}
```

Default format is: 

```
{{default_human_format()}}
```

Of course, you can change this format with for example:

```python
{{ code_example("format1bis.py") }}
```

```
{{ code_example_to_output("format1bis.py") }}
```

??? note "`{extras}` format?"

    By default, `HumanFormatter` use a `LogFmtKVFormatter` for formatting the `{extras}` placeholder. Of course, you 
    can change or tune that by providing your own instance of `KVFormatter` to `HumanFormatter` object.

## `RichHumanFormatter`

This formatter can be used to get a human friendly output (with {{rich}} library installed).

Default format is: 

```
{{default_rich_human_format()}}
```

This formatter provides some custom placeholders:

- `{rich_escaped_message}`: the standard `{message}` placeholder but [escaped](https://rich.readthedocs.io/en/stable/markup.html#escaping) to avoid some accidental rich markup rendering inside message
- `{rich_escaped_extras}`: same thing but for `{extras}` placeholder
- `{rich_level_style}`: contain a smart rich markup style depending on the log level

??? note "`{extras}/{rich_escaped_extras}` format?"

    By default, `RichHumanFormatter` use a `LogFmtKVFormatter` for formatting the `{extras}` placeholder with custom
    attributes:

    -  `prefix="\n    :arrow_right_hook: "`
    - `suffix=""`
    - `template="[repr.attrib_name]{key}[/repr.attrib_name][repr.attrib_equal]=[/repr.attrib_equal][repr.attrib_value]{value}[/repr.attrib_value]"`

    Of course, you can change or tune that by providing your own instance of `KVFormatter` to `HumanFormatter` object.

## `LogFmtFormatter`

This formatter will format your logs with the {{logfmt}}.

Default format is: 

```
{{default_logfmt_format()}}
```

But the use of this format is **special** with this formatter as placeholders can be encoded to be valid for {{logfmt}}. So to configure an alternate format:

- use the `key={placeholder}` syntax (with space separated key/values blocs)
- don't try to escape or quote your values , it will be done automatically and dynamically, so don't use quotes in your format
- use the placeholder `{extras}` alone at the end (without leading space) to get all extra key/values

```python
{{ code_example("format5.py") }}
```

{{ code_example_to_svg("format5.py") }}

## `JsonFormatter`

This formatter will format your logs in the JSON format.

Default format is:

```
{{default_json_format()}}
```

But the use of this format is **special** with this formatter as placeholders can be encoded to be valid for JSON. So to configure an alternate format:

- provide a nearly JSON valid format (except for placeholders, see next item)
- don't try to escape your values, it will be done automatically and dynamically, so don't use quotes in your format around placeholders
- there is no `{extras}` placeholder (see below)

??? question "What about `{extras}` placeholder in JSON format?"

    Extra key/values are automatically injected in the JSON as root keys if `include_extras_in_key=""` (default).

    You can include all extras keys as a child dict or another root key by using for example: `includes_extras_in_key="extras"` to get
    something like:

    ```json
    {
        "time": "2023-01-01T12:13:14Z",
        "logger": "foo",
        "level": "CRITICAL",
        "message": "Houston we have a problem",
        "extras": {
            "foo": "bar",
            "foo2": "bar2",
        }
    }

    Note: you can also use `include_extras_in_key=None` to remove all extras key/values from output.
    ```


## Available Environment variables

As we love {{twelvefactorapp}} plenty of default behavior of `stlog` can be configured with environment variables.

!!! note "configuration priority?"

    In order of importance (the last one wins):

    - default values (set in the code)
    - environment variables
    - explicit configuration in the code (always wins)

### `STLOG_USE_RICH`

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

### `STLOG_READ_EXTRA_KWARGS_FROM_STANDARD_LOGGING`

This variable can change the default value of `read_extra_kwarg_from_standard_logging` parameter of the {{apilink("setup")}} function: 

- if set to `1`, `TRUE`, `YES`: default value of `read_extra_kwarg_from_standard_logging` is set to `True`

### `STLOG_ENV_JSON_CONTEXT` and `STLOG_ENV_CONTEXT_*`

These variables can be used to inject a global context. See [usage documentation](../usage) for details.

### `STLOG_UNIT_TESTS_MODE`

!!! warning "Private feature!"

    This is a private feature (DON'T USE IT) to get always the same output (fixed date, fixed process number...)

### FIXME (document)

- STLOG_IGNORE_COMPOUND_TYPES
- STLOG_PROGRAM_NAME