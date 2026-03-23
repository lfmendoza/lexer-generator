from __future__ import annotations

from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def repo_root() -> Path:
    return _REPO


@pytest.fixture
def arithmetic_spec_yal(repo_root: Path) -> Path:
    return repo_root / "specs" / "yal" / "arithmetic_expression.yal"


@pytest.fixture
def arithmetic_sample_txt(repo_root: Path) -> Path:
    return repo_root / "samples" / "inputs" / "arithmetic_expressions.txt"
