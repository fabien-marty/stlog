from __future__ import annotations


def define_env(env):
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
