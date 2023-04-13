from __future__ import annotations

from jinja2_shell_extension import shell  # type: ignore


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
                title = obj
            else:
                title = "API reference"
        return f"[{title}]({url})"
