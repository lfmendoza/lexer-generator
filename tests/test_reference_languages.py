"""PICO y ArnoldC: tokens y error léxico en muestra inválida."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from yalex.pipeline import CompileOptions, compile_from_file


@pytest.fixture
def pico_spec_yal(repo_root: Path) -> Path:
    return repo_root / "specs" / "yal" / "pico.yal"


@pytest.fixture
def arnoldc_spec_yal(repo_root: Path) -> Path:
    return repo_root / "specs" / "yal" / "arnoldc.yal"


def _compile_and_run(lexer_py: Path, input_path: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(lexer_py), str(input_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_pico_hello_sample_token_sequence(
    tmp_path: Path,
    pico_spec_yal: Path,
    repo_root: Path,
) -> None:
    base = str(tmp_path / "pico_lexer")
    compile_from_file(
        str(pico_spec_yal),
        CompileOptions(output_name=base, emit_trees=False, emit_dfa_graph=False),
    )
    lexer_py = tmp_path / "pico_lexer.py"
    assert lexer_py.is_file()
    hello = repo_root / "samples" / "inputs" / "pico" / "hello.pico"
    code, out, err = _compile_and_run(lexer_py, hello)
    assert code == 0, err
    types = re.findall(r"^\('([^']+)'", out, flags=re.MULTILINE)
    assert types == [
        "KW_LET",
        "IDENT",
        "ASSIGN",
        "STRING_LIT",
        "SEMICOLON",
        "KW_EMIT",
        "STRING_LIT",
        "SEMICOLON",
        "KW_EMIT",
        "IDENT",
        "SEMICOLON",
    ]


def test_pico_invalid_input_lexical_error_location(
    tmp_path: Path,
    pico_spec_yal: Path,
    repo_root: Path,
) -> None:
    base = str(tmp_path / "pico_lexer")
    compile_from_file(
        str(pico_spec_yal),
        CompileOptions(output_name=base, emit_trees=False, emit_dfa_graph=False),
    )
    lexer_py = tmp_path / "pico_lexer.py"
    bad = repo_root / "samples" / "inputs" / "pico" / "invalid_char.pico"
    code, out, err = _compile_and_run(lexer_py, bad)
    assert code == 1
    assert "LEXICAL ERROR at line 3, column 12" in err
    assert "'@'" in err or "@'" in err


def test_arnoldc_minimal_program_tokens(
    tmp_path: Path,
    arnoldc_spec_yal: Path,
    repo_root: Path,
) -> None:
    base = str(tmp_path / "arnoldc_lexer")
    compile_from_file(
        str(arnoldc_spec_yal),
        CompileOptions(output_name=base, emit_trees=False, emit_dfa_graph=False),
    )
    lexer_py = tmp_path / "arnoldc_lexer.py"
    hello = repo_root / "samples" / "inputs" / "arnoldc" / "hello.arnoldc"
    code, out, err = _compile_and_run(lexer_py, hello)
    assert code == 0, err
    assert "KW_MAIN_START" in out and "KW_PRINT" in out and "KW_MAIN_END" in out
