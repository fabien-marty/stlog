from __future__ import annotations

import datetime
import sys
from typing import Any

import jinja2
from yaml import Loader, load

YEAR = datetime.datetime.utcnow().year


def compare_lines(content1: str, content2: str) -> bool:
    lines = zip(content1.splitlines(), content2.splitlines())
    for i, tpl in enumerate(lines):
        if str(YEAR) + "-" in tpl[0]:
            continue
        if "process" in tpl[0]:
            continue
        if "thread" in tpl[0]:
            continue
        if len(tpl) != 2:
            print("missing line")
            return False
        if tpl[0] != tpl[1]:
            print("changed line: %i '%s' != '%s'" % (i, tpl[0], tpl[1]))
            return False
    return True


def get_variables() -> dict[str, Any]:
    with open("mkdocs.yml") as f:
        data = load(f, Loader=Loader)
        data["extra"]["pathprefix"] = "docs/"
        return data["extra"]


env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("."),
    extensions=["jinja2_shell_extension.ShellExtension"],
)
template = env.get_template("README.md.j2")
variables = get_variables()
if len(sys.argv) >= 2 and sys.argv[1] == "lint":
    variables["linting"] = "--linting"
res = template.render(**variables)
res = (
    """
<!-- WARNING: generated from README.md.j2, do not modify this file manually but modify README.md.j2 instead
     and execute 'poetry run poe make_readme' to regenerate this README.md file -->

"""
    + res
)
if variables.get("linting"):
    with open("README.md") as f:
        to_compare = f.read().strip()
    if not compare_lines(to_compare, res.strip()):
        sys.exit(1)
else:
    with open("README.md", "w") as f:
        f.write(res)
