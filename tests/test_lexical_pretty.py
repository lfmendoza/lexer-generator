"""Salida --pretty del lexer generado."""

from __future__ import annotations

import io
import runpy
import sys
from pathlib import Path

from yalex.pipeline import CompileOptions, compile_from_file


def test_pretty_view_contains_types_line(
    tmp_path: Path,
    arithmetic_spec_yal: Path,
    arithmetic_sample_txt: Path,
) -> None:
    opts = CompileOptions(
        output_name=str(tmp_path / "lex_pretty"),
        emit_trees=False,
        emit_dfa_graph=False,
    )
    result = compile_from_file(str(arithmetic_spec_yal), opts)
    buf = io.StringIO()
    old_out, old_argv = sys.stdout, sys.argv
    try:
        sys.argv = [result.output_path, str(arithmetic_sample_txt), "--pretty"]
        sys.stdout = buf
        runpy.run_path(result.output_path, run_name="__main__")
    finally:
        sys.stdout = old_out
        sys.argv = old_argv

    out = buf.getvalue()
    assert "=== Vista léxica" in out or "=== Vista lexica" in out
    assert "Tipos:" in out
    assert "ID ASSIGN NUMBER PLUS NUMBER" in out
