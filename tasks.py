from __future__ import annotations

from invoke import UnexpectedExit, task

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
def lint_readme(c, fix=True):
    """Lint the README"""
    try:
        c.run("python make_readme.py lint")
    except UnexpectedExit:
        readme(c)
        lint_readme(c, fix=False)


@task
def readme(c):
    """Make the README"""
    c.run("python make_readme.py")


@task
def lint_imports(c):
    """Lint the code with import-linter"""
    c.run("lint-imports --debug --config pyproject.toml")


@task(help={"fix": "try to automatically fix the code (default)"})
def lint(c, fix=True):
    """Lint the code with all linters"""
    lint_ruff(c, fix=fix)
    lint_black(c, fix=fix)
    lint_mypy(c)
    lint_imports(c)
    lint_readme(c, fix=fix)


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


@task(apidoc, doc, readme)
def docs(c):
    pass
