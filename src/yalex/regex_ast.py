"""Abstract syntax tree for YALex regular expressions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

# Regex AST nodes


@dataclass
class ReLiteral:
    """Single character."""

    char: int  # ordinal


@dataclass
class ReCharClass:
    """Set of characters (possibly negated)."""

    chars: set[int]
    negated: bool = False

    def effective_chars(self) -> set[int]:
        if self.negated:
            return set(range(0, 128)) - self.chars
        return set(self.chars)


@dataclass
class ReConcat:
    left: RegexNode
    right: RegexNode


@dataclass
class ReUnion:
    left: RegexNode
    right: RegexNode


@dataclass
class ReStar:
    child: RegexNode


@dataclass
class RePlus:
    child: RegexNode


@dataclass
class ReOptional:
    child: RegexNode


@dataclass
class ReDifference:
    """Set difference: left # right (both must be char classes)."""

    left: RegexNode
    right: RegexNode


@dataclass
class ReAny:
    """Wildcard _ : matches any character."""

    pass


@dataclass
class ReEOF:
    """Special EOF marker."""

    pass


@dataclass
class ReEndMarker:
    """End-marker for direct DFA construction."""

    rule_index: int


RegexNode: TypeAlias = (
    ReLiteral
    | ReCharClass
    | ReConcat
    | ReUnion
    | ReStar
    | RePlus
    | ReOptional
    | ReDifference
    | ReAny
    | ReEOF
    | ReEndMarker
)
