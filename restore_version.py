from __future__ import annotations

import os
import shutil

try:
    shutil.copyfile("stlog/__init__.py.restore_version", "stlog/__init__.py")
except Exception:
    pass

try:
    shutil.copyfile("pyproject.toml.restore_version", "pyproject.toml")
except Exception:
    pass

try:
    os.unlink("stlog/__init__.py.restore_version")
except Exception:
    pass

try:
    os.unlink("pyproject.toml.restore_version")
except Exception:
    pass
