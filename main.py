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
            url = env.variables["_apilink"] + "#stlog." + obj
        if not title:
            if obj:
                title = f"`{obj}`"
            else:
                title = "API reference"
        return f"[{title}]({url})"
