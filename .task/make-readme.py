from __future__ import annotations

import difflib
import os
import sys
from typing import Any

import jinja2
from yaml import Loader, load


def readme(lint=False):
    if lint:
        print("linting readme...")
    else:
        print("making readme...")
    os.environ["STLOG_UNIT_TESTS_MODE"] = "1"

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
    res = template.render(**variables)
    res = (
        """
 <!-- WARNING: generated from README.md.j2, do not modify this file manually but modify README.md.j2 instead
      and execute 'poetry run invoke readme' to regenerate this README.md file -->

 """
        + res
    )
    if lint:
        with open("README.md") as f:
            to_compare = f.read()
        if to_compare != res:
            print("README.md must be rebuilt")
            print()
            sys.stdout.writelines(
                difflib.unified_diff(
                    to_compare.splitlines(),
                    res.splitlines(),
                    fromfile="README.md",
                    tofile="new README.md",
                )
            )
            print()
            print("use 'poetry run invoke readme' to do that")
            sys.exit(1)
    else:
        with open("README.md", "w") as f:
            f.write(res)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate or lint README.md file")
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Lint the README.md file instead of generating it",
    )
    args = parser.parse_args()

    readme(lint=args.lint)
