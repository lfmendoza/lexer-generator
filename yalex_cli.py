#!/usr/bin/env python3
"""CLI entry when the package is not installed (see README)."""

from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent
_src = _root / "src"
if _src.is_dir() and str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from yalex.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
