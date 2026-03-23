"""Tests for .yal specification parsing."""

from __future__ import annotations

import pytest

from yalex.diagnostics import SpecParseError
from yalex.spec_parser import parse_yalex_string


def test_parse_minimal_rule_section() -> None:
    src = """
rule tokens =
  'a' { return 'A' }
"""
    spec = parse_yalex_string(src)
    assert spec.entrypoint == "tokens"
    assert len(spec.rules) == 1
    assert "'a'" in spec.rules[0].pattern_str


def test_let_without_equals_errors() -> None:
    src = """
let foo
rule tokens =
  'a' { }
"""
    with pytest.raises(SpecParseError):
        parse_yalex_string(src)
