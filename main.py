# python code for mkdocs macros plugin

from __future__ import annotations

import os

from jinja2_shell_extension import shell  # type: ignore

os.environ["STLOG_UNIT_TESTS_MODE"] = "1"


def define_env(env):
    env.filters["shell"] = shell

    @env.macro
    def apilink(obj: str = "", title: str = ""):
        if not obj:
            url = env.variables["_apilink"]
        else:
            tmp = obj.split(".")
            if len(tmp) == 2:
                url = env.variables["_apilink"] + f"{tmp[0]}.html#stlog.{obj}"
            else:
                url = env.variables["_apilink"] + "#stlog." + obj
        if not title:
            if obj:
                title = f"`{obj}`"
            else:
                title = "API reference"
        return f"[{title}]({url})"

    @env.macro
    def code_example(filename: str):
        with open(f"./docs/python/{filename}") as f:
            return f.read()

    @env.macro
    def code_example_to_svg(
        filename: str, interpreter: str = "python", lines: int = 10
    ):
        cmd = f"python ./docs/python/termtosvg.py --interpreter={interpreter} --lines={lines} {filename}"
        return shell(None, cmd, die_on_error=True)

    @env.macro
    def code_example_to_output(filename: str, interpreter: str = "python"):
        cmd = f"STLOG_USE_RICH=0 ; {interpreter} docs/python/{filename}"
        return shell(None, cmd, die_on_error=True)
