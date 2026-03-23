"""Golden: arithmetic_expression.yal on arithmetic_expressions.txt."""

from __future__ import annotations

import io
import runpy
import sys
from pathlib import Path

from yalex.pipeline import CompileOptions, compile_from_file


def test_golden_tokens_arithmetic(
    tmp_path: Path,
    arithmetic_spec_yal: Path,
    arithmetic_sample_txt: Path,
    repo_root: Path,
) -> None:
    expected_path = repo_root / "tests" / "fixtures" / "expected_tokens.txt"
    expected = expected_path.read_text(encoding="utf-8")

    base = str(tmp_path / "lexer_out")
    opts = CompileOptions(
        output_name=base,
        emit_trees=False,
        emit_dfa_graph=False,
    )
    result = compile_from_file(str(arithmetic_spec_yal), opts)
    assert result.output_path == base + ".py"

    buf = io.StringIO()
    old_out, old_argv = sys.stdout, sys.argv
    try:
        sys.argv = [result.output_path, str(arithmetic_sample_txt)]
        sys.stdout = buf
        runpy.run_path(result.output_path, run_name="__main__")
    finally:
        sys.stdout = old_out
        sys.argv = old_argv

    assert buf.getvalue() == expected
