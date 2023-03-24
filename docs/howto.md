# Howto

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

## Second, you can use `STLOG_CONTEXT_*` env var 

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