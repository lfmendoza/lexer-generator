"""Comportamiento del lexer generado y del pipeline (DOT, longest match, regex, eof)."""

from __future__ import annotations

import io
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

import yalex.dot as dot_mod
from yalex.pipeline import CompileOptions, build_combined_dfa, compile_from_file
from yalex.spec_parser import parse_yalex_string


@pytest.fixture(autouse=True)
def _skip_graphviz_png_during_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dot_mod, "_try_render_dot", lambda _path: None)


def test_default_compile_emits_expression_tree_dots(tmp_path: Path) -> None:
    tiny = tmp_path / "tiny.yal"
    tiny.write_text(
        """
{
}
let lit = 'x'
rule gettoken =
  | lit                           { return ('X', lxm, line, col) }
  | eof                           { raise EOFError('e') }
""".strip(),
        encoding="utf-8",
    )
    base = str(tmp_path / "sem_lex")
    opts = CompileOptions(
        output_name=base,
        emit_trees=True,
        emit_dfa_graph=False,
        emit_info_messages=False,
    )
    compile_from_file(str(tiny), opts)
    tree_dir = tmp_path / "sem_lex_trees"
    assert tree_dir.is_dir()
    assert (tree_dir / "combined.dot").is_file()
    assert (tree_dir / "def_lit.dot").is_file()
    assert (tree_dir / "rule_0.dot").is_file()
    text = (tree_dir / "combined.dot").read_text(encoding="utf-8")
    assert "digraph ExprTree" in text


def test_compile_options_emit_trees_true_by_default() -> None:
    assert CompileOptions().emit_trees is True


def test_longest_match_prefers_two_character_operator(tmp_path: Path) -> None:
    yal = """
{
}
let letter = ['a'-'z']
let id = letter+
rule gettoken =
  | "=="                          { return ('EQ', lxm, line, col) }
  | '='                           { return ('ASSIGN', lxm, line, col) }
  | id                            { return ('ID', lxm, line, col) }
"""
    spec = parse_yalex_string(yal.strip(), "<longest>")
    base = str(tmp_path / "lm")
    compile_from_file(
        "<longest>",
        CompileOptions(output_name=base, emit_trees=False, emit_dfa_graph=False),
        spec=spec,
    )
    lexer_py = tmp_path / "lm.py"
    buf = io.StringIO()
    old_out, old_argv = sys.stdout, sys.argv
    try:
        sys.argv = [str(lexer_py), str(tmp_path / "in.txt")]
        sys.stdout = buf
        (tmp_path / "in.txt").write_text("a==b", encoding="utf-8")
        runpy.run_path(str(lexer_py), run_name="__main__")
    finally:
        sys.stdout = old_out
        sys.argv = old_argv
    out = buf.getvalue()
    assert "('EQ'" in out
    assert out.count("'ID'") == 2


def test_rule_priority_keyword_before_identifier_same_length(tmp_path: Path) -> None:
    yal = """
{
}
let letter = ['a'-'z']
let id = letter+
rule gettoken =
  | "if"                          { return ('IF', lxm, line, col) }
  | id                            { return ('ID', lxm, line, col) }
"""
    spec = parse_yalex_string(yal.strip(), "<prio>")
    base = str(tmp_path / "pr")
    compile_from_file(
        "<prio>",
        CompileOptions(output_name=base, emit_trees=False, emit_dfa_graph=False),
        spec=spec,
    )
    lexer_py = tmp_path / "pr.py"
    buf = io.StringIO()
    old_out, old_argv = sys.stdout, sys.argv
    try:
        sys.argv = [str(lexer_py), str(tmp_path / "kw.txt")]
        sys.stdout = buf
        (tmp_path / "kw.txt").write_text("if", encoding="utf-8")
        runpy.run_path(str(lexer_py), run_name="__main__")
    finally:
        sys.stdout = old_out
        sys.argv = old_argv
    assert "('IF'" in buf.getvalue()


def test_regex_operators_star_plus_question_union_class_negated_difference_build_dfa() -> None:
    yal = """
{
}
let diff = ['a'-'d'] # ['b']
let star = ('x')*
let plus = 'y'+
let opt = 'z'?
let alt = 'p' | 'q'
let neg = [^ '0'-'9' '\n']
rule gettoken =
  | diff                          { return ('DIFF', lxm, line, col) }
  | star                          { return ('STAR', lxm, line, col) }
  | plus                          { return ('PLUS', lxm, line, col) }
  | opt                           { return ('OPT', lxm, line, col) }
  | alt                           { return ('ALT', lxm, line, col) }
  | neg                           { return ('NEG', lxm, line, col) }
"""
    spec = parse_yalex_string(yal.strip(), "<ops>")
    states, _start, _actions = build_combined_dfa(spec)
    assert len(states) >= 1


def test_eof_rule_on_empty_input_exits_cleanly(tmp_path: Path) -> None:
    yal = """
{
}
rule gettoken =
  | 'a'                           { return ('A', lxm, line, col) }
  | eof                           { raise EOFError('end') }
"""
    spec = parse_yalex_string(yal.strip(), "<eof>")
    base = str(tmp_path / "eof")
    compile_from_file(
        "<eof>",
        CompileOptions(output_name=base, emit_trees=False, emit_dfa_graph=False),
        spec=spec,
    )
    lexer_py = tmp_path / "eof.py"
    (tmp_path / "empty.txt").write_text("", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(lexer_py), str(tmp_path / "empty.txt")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert proc.returncode == 0
    assert "TOKENS" in proc.stdout
