"""Corpus bajo samples/inputs: ejecución sin LexerError."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from yalex.pipeline import CompileOptions, compile_from_file


def _run_lexer(lexer_py: Path, input_path: Path) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(lexer_py), str(input_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _compile(tmp_path: Path, spec: Path, base_name: str) -> Path:
    base = str(tmp_path / base_name)
    compile_from_file(
        str(spec),
        CompileOptions(output_name=base, emit_trees=False, emit_dfa_graph=False),
    )
    return tmp_path / f"{base_name}.py"


@pytest.mark.parametrize(
    "input_name",
    [
        "arithmetic_expressions.txt",
        "arithmetic_edge_cases.txt",
        "arithmetic_comprehensive.txt",
    ],
)
def test_arithmetic_corpus_files(
    tmp_path: Path,
    repo_root: Path,
    arithmetic_spec_yal: Path,
    input_name: str,
) -> None:
    lexer_py = _compile(tmp_path, arithmetic_spec_yal, "arith_lex")
    inp = repo_root / "samples" / "inputs" / input_name
    code, out, err = _run_lexer(lexer_py, inp)
    assert code == 0, (err, out)
    assert "tokens found" in out
    assert "LEXICAL ERROR" not in err


@pytest.mark.parametrize(
    "input_name",
    [
        "imperative_core_sample.txt",
        "imperative_comprehensive.txt",
    ],
)
def test_imperative_corpus_files(
    tmp_path: Path,
    repo_root: Path,
    imperative_spec_yal: Path,
    input_name: str,
) -> None:
    lexer_py = _compile(tmp_path, imperative_spec_yal, "imp_lex")
    inp = repo_root / "samples" / "inputs" / input_name
    code, out, err = _run_lexer(lexer_py, inp)
    assert code == 0, (err, out)
    assert "tokens found" in out
    ntok = int(out.strip().split("tokens found")[0].strip().split()[-1])
    assert ntok >= 10


@pytest.fixture
def imperative_spec_yal(repo_root: Path) -> Path:
    return repo_root / "specs" / "yal" / "imperative_core.yal"


def _pico_success_files(repo_root: Path) -> list[Path]:
    d = repo_root / "samples" / "inputs" / "pico"
    return sorted(
        p
        for p in d.glob("*.pico")
        if p.name != "invalid_char.pico"
    )


@pytest.mark.parametrize(
    "input_path",
    _pico_success_files(Path(__file__).resolve().parents[1]),
    ids=lambda p: p.name,
)
def test_pico_corpus_each_file(
    tmp_path: Path,
    pico_spec_yal: Path,
    input_path: Path,
) -> None:
    lexer_py = _compile(tmp_path, pico_spec_yal, "pico_lex")
    code, out, err = _run_lexer(lexer_py, input_path)
    assert code == 0, (input_path.name, err, out)
    assert "LEXICAL ERROR" not in err


@pytest.fixture
def pico_spec_yal(repo_root: Path) -> Path:
    return repo_root / "specs" / "yal" / "pico.yal"


def _arnoldc_files(repo_root: Path) -> list[Path]:
    return sorted((repo_root / "samples" / "inputs" / "arnoldc").glob("*.arnoldc"))


@pytest.mark.parametrize(
    "input_path",
    _arnoldc_files(Path(__file__).resolve().parents[1]),
    ids=lambda p: p.name,
)
def test_arnoldc_corpus_each_file(
    tmp_path: Path,
    arnoldc_spec_yal: Path,
    input_path: Path,
) -> None:
    lexer_py = _compile(tmp_path, arnoldc_spec_yal, "arn_lex")
    code, out, err = _run_lexer(lexer_py, input_path)
    assert code == 0, (input_path.name, err, out)
    assert "LEXICAL ERROR" not in err


@pytest.fixture
def arnoldc_spec_yal(repo_root: Path) -> Path:
    return repo_root / "specs" / "yal" / "arnoldc.yal"


def test_imperative_comprehensive_token_volume(
    tmp_path: Path,
    repo_root: Path,
    imperative_spec_yal: Path,
) -> None:
    lexer_py = _compile(tmp_path, imperative_spec_yal, "imp_lex")
    inp = repo_root / "samples" / "inputs" / "imperative_comprehensive.txt"
    code, out, err = _run_lexer(lexer_py, inp)
    assert code == 0, err
    ntok = int(out.strip().split("tokens found")[0].strip().split()[-1])
    assert ntok >= 200
