from __future__ import annotations

import datetime
import hashlib
import sys
from typing import Any

import jinja2
from yaml import Loader, load

YEAR = datetime.datetime.utcnow().year


def get_special_hash(content: str) -> str:
    to_hash = [
        x
        for x in content.splitlines()
        if (str(YEAR) + "-") not in x and "process" not in x and "thread" not in x
    ]
    return hashlib.sha1("\n".join(to_hash).encode("utf-8")).hexdigest()


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
if len(sys.argv) >= 2 and sys.argv[1] == "lint":  # noqa: PLR2004
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
    if get_special_hash(to_compare) != get_special_hash(res.strip()):
        print(
            "ERROR: README.md must be generated => execute 'poetry run poe make_readme' and commit result"
        )
        sys.exit(1)
else:
    with open("README.md", "w") as f:
        f.write(res)
