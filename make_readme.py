from __future__ import annotations

import sys
from typing import Any

import jinja2
from yaml import Loader, load


def get_variables() -> dict[str, Any]:
    with open("mkdocs.yml") as f:
        data = load(f, Loader=Loader)
        data["extra"]["pathprefix"] = "docs/"
        return data["extra"]


env = jinja2.Environment(loader=jinja2.FileSystemLoader("."))
template = env.get_template("README.md.j2")
res = template.render(**get_variables())
res = (
    """
<!-- WARNING: generated from README.md.j2, do not modify this file manually but modify README.md.j2 instead
     and execute 'poetry run poe make_readme' to regenerate this README.md file -->

"""
    + res
)
if len(sys.argv) >= 2 and sys.argv[1] == "lint":  # noqa: PLR2004
    with open("README.md") as f:
        to_compare = f.read().strip()
    if to_compare != res.strip():
        print(
            "ERROR: README.md must be generated => execute 'poetry run poe make_readme' and commit result"
        )
        sys.exit(1)
else:
    with open("README.md", "w") as f:
        f.write(res)
