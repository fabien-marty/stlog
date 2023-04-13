from __future__ import annotations

import difflib
import os
import sys
from typing import Any

import jinja2
from invoke import task
from yaml import Loader, load

PACKAGE = "stlog"


def _clean_core(c):
    c.run(
        "rm -Rf .*_cache build ; find . -type d -name __pycache__ -exec rm -Rf {} \\; 2>/dev/null"
    )


def _clean_coverage(c):
    c.run("rm -Rf htmlcov")


def _clean_apidoc(c):
    c.run("rm -Rf apihtml")


def _clean_doc(c):
    c.run("rm -Rf html")


@task
def clean(c):
    """Clean the repository"""
    _clean_core(c)
    _clean_coverage(c)
    _clean_apidoc(c)
    _clean_doc(c)


@task
def doc(c):
    """Make user documentation"""
    _clean_doc(c)
    c.run("mkdocs build --site-dir html")


@task(
    help={
        "port": "TCP port to use (default: 9090)",
        "bind": "IP address to bind (0.0.0.0 for all, default: 127.0.0.0.1)",
    }
)
def serve_doc(c, port=9090, bind="127.0.0.1"):
    """Serve the user documentation (dev mode)"""
    _clean_doc(c)
    c.run("mkdocs serve --livereload --dirtyreload --dev-addr=${bind}:${port}")


@task(help={"fix": "try to automatically fix the code (default)"})
def lint_ruff(c, fix=True):
    """Lint the code with ruff"""
    if fix:
        c.run("ruff . --fix")
    else:
        c.run("ruff .")


@task(help={"fix": "try to automatically fix the code (default)"})
def lint_black(c, fix=True):
    """Lint the code with black"""
    if fix:
        c.run("black .")
    else:
        c.run("black --check .")


@task
def lint_mypy(c):
    """Lint the code with mypy"""
    c.run("mypy --check-untyped-defs .")


@task(help={"fix": "try to automatically fix the code (default)"})
def lint(c, fix=True):
    """Lint the code with all linters"""
    lint_ruff(c, fix=fix)
    lint_black(c, fix=fix)
    lint_mypy(c)
    readme(c, lint=not fix)


@task(help={"coverage": "compute converage"})
def test(c, coverage=False):
    """Execute unit tests"""
    if coverage:
        _clean_coverage(c)
        c.run(
            f"pytest --no-cov-on-fail --cov={PACKAGE} --cov-report=term --cov-report=html --cov-report=xml tests/"
        )
    else:
        c.run("pytest .")


@task
def apidoc(c):
    """Make API doc"""
    _clean_apidoc(c)
    c.run(f"pdoc3 --html --output-dir=apihtml {PACKAGE}")


@task
def readme(c, lint=False):
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

    if os.environ.get("CI", "false") == "true":
        print("CI MODE => we do nothing")
        sys.exit(0)

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


@task(apidoc, doc, readme)
def docs(c):
    pass
