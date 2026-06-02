"""Generación de árboles de regex (DOT) para cada spec en specs/yal/."""

from __future__ import annotations

from pathlib import Path

import pytest

import yalex.dot as dot_mod
from yalex.pipeline import CompileOptions, compile_from_file
from yalex.spec_parser import parse_yalex_file

_REPO = Path(__file__).resolve().parents[1]
PROJECT_YAL_SPECS = sorted((_REPO / "specs" / "yal").glob("*.yal"))


@pytest.fixture(autouse=True)
def _no_graphviz_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dot_mod, "_try_render_dot", lambda _path: None)


def _expected_dot_names(spec_path: Path) -> list[str]:
    spec = parse_yalex_file(str(spec_path))
    names = [f"def_{name}.dot" for name, _ in spec.definitions]
    names.extend(f"rule_{i}.dot" for i in range(len(spec.rules)))
    if spec.rules:
        names.append("combined.dot")
    return names


def test_project_yal_specs_discovered() -> None:
    assert PROJECT_YAL_SPECS, "debe haber al menos un .yal en specs/yal/"


@pytest.mark.parametrize("yal_path", PROJECT_YAL_SPECS, ids=lambda p: p.stem)
def test_compile_emits_all_expression_trees(yal_path: Path, tmp_path: Path) -> None:
    base = tmp_path / f"lex_{yal_path.stem}"
    compile_from_file(
        str(yal_path),
        CompileOptions(
            output_name=str(base),
            emit_trees=True,
            emit_dfa_graph=False,
            emit_info_messages=False,
        ),
    )
    tree_dir = Path(f"{base}_trees")
    assert tree_dir.is_dir()
    for dot_name in _expected_dot_names(yal_path):
        dot_file = tree_dir / dot_name
        assert dot_file.is_file(), f"expected {dot_name} under {tree_dir}"
        text = dot_file.read_text(encoding="utf-8")
        assert text.lstrip().startswith("digraph ExprTree"), dot_name
