"""Pytest bootstrap for running the test suite from a source checkout.

Keep the repository root importable even when pytest is launched via its
console-script entry point, whose sys.path[0] may point at the interpreter's
bin directory instead of this checkout.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)
