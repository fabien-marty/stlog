# Dev

- managed by `poetry` and [`invoke`](https://docs.pyinvoke.org/) as a task launcher
- `poetry run invoke --list` to see available tasks (linting, unit tests, reformating...):

```
{{ "invoke --list"|shell() }}
```

[Coverage]({{coverage}})
