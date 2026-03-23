"""Tests for regex AST parsing."""

from __future__ import annotations

import pytest

from yalex.diagnostics import RegexParseError
from yalex.regex_ast import ReCharClass, ReConcat, ReUnion
from yalex.regex_parser import RegexParser


def test_union_and_concat() -> None:
    p = RegexParser("'a'|\"bc\"", {})
    node = p.parse()
    assert isinstance(node, ReUnion)
    assert isinstance(node.right, ReConcat)


def test_char_class() -> None:
    p = RegexParser("[a-z]", {})
    node = p.parse()
    assert isinstance(node, ReCharClass)
    assert ord("a") in node.chars


def test_undefined_ident() -> None:
    p = RegexParser("unknown", {})
    with pytest.raises(RegexParseError, match="Undefined"):
        p.parse()
