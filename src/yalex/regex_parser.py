"""Parse YALex regex syntax into an AST."""

from __future__ import annotations

from yalex.diagnostics import RegexParseError
from yalex.regex_ast import (
    ReAny,
    ReCharClass,
    ReConcat,
    ReEOF,
    RegexNode,
    ReLiteral,
    ReOptional,
    RePlus,
    ReStar,
    ReUnion,
)


class RegexParser:
    """
    Parses YALex regex syntax into AST nodes.

    Precedence (low to high):
        |  (union)
        concat
        * + ?
        # (set difference)
    """

    def __init__(self, text: str, definitions: dict[str, str]) -> None:
        self.text = text
        self.pos = 0
        self.definitions = definitions
        self.parsed_defs: dict[str, RegexNode] = {}

    def parse(self) -> RegexNode:
        return self._expr()

    def _peek(self) -> str | None:
        self._skip_ws()
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None

    def _skip_ws(self) -> None:
        while self.pos < len(self.text) and self.text[self.pos] in " \t":
            self.pos += 1

    def _expr(self) -> RegexNode:
        left = self._concat()
        while self._peek() == "|":
            self.pos += 1
            right = self._concat()
            left = ReUnion(left, right)
        return left

    def _concat(self) -> RegexNode:
        node = self._unary()
        while True:
            p = self._peek()
            if p is None or p in "|)":
                break
            if p in "([\'\"_" or (p.isalnum() and p != "|") or p == "[":
                right = self._unary()
                node = ReConcat(node, right)
            else:
                break
        return node

    def _unary(self) -> RegexNode:
        node = self._diff()
        while self._peek() in ("*", "+", "?"):
            op = self.text[self.pos]
            self.pos += 1
            if op == "*":
                node = ReStar(node)
            elif op == "+":
                node = RePlus(node)
            elif op == "?":
                node = ReOptional(node)
        return node

    def _diff(self) -> RegexNode:
        node = self._primary()
        while self._peek() == "#":
            self.pos += 1
            right = self._primary()
            left_chars = self._resolve_charset(node)
            right_chars = self._resolve_charset(right)
            diff_chars = left_chars - right_chars
            node = ReCharClass(diff_chars)
        return node

    def _resolve_charset(self, node: RegexNode) -> set[int]:
        if isinstance(node, ReCharClass):
            return node.effective_chars()
        elif isinstance(node, ReLiteral):
            return {node.char}
        elif isinstance(node, ReAny):
            return set(range(0, 128))
        else:
            raise RegexParseError(
                f"Cannot resolve charset from {type(node).__name__}",
                self.pos,
            )

    def _primary(self) -> RegexNode:
        self._skip_ws()
        if self.pos >= len(self.text):
            raise RegexParseError("Unexpected end of regex", self.pos)

        ch = self.text[self.pos]

        if ch == "[":
            return self._parse_charclass()

        if ch == "(":
            self.pos += 1
            node = self._expr()
            self._skip_ws()
            if self.pos < len(self.text) and self.text[self.pos] == ")":
                self.pos += 1
            return node

        if ch == "'":
            return self._parse_char_literal()

        if ch == '"':
            return self._parse_string_literal()

        if ch == "_" and (
            self.pos + 1 >= len(self.text) or not self.text[self.pos + 1].isalnum()
        ):
            self.pos += 1
            return ReAny()

        if ch.isalpha() or ch == "_":
            ident = self._read_ident()
            if ident == "eof":
                return ReEOF()
            if ident in self.definitions:
                if ident not in self.parsed_defs:
                    sub_parser = RegexParser(self.definitions[ident], self.definitions)
                    sub_parser.parsed_defs = self.parsed_defs
                    self.parsed_defs[ident] = sub_parser.parse()
                return self.parsed_defs[ident]
            raise RegexParseError(f"Undefined identifier: {ident}", self.pos)

        raise RegexParseError(
            f"Unexpected character {ch!r} at position {self.pos} in regex: {self.text!r}",
            self.pos,
        )

    def _read_ident(self) -> str:
        start = self.pos
        while self.pos < len(self.text) and (
            self.text[self.pos].isalnum() or self.text[self.pos] == "_"
        ):
            self.pos += 1
        return self.text[start : self.pos]

    def _parse_char_literal(self) -> ReLiteral:
        if self.pos >= len(self.text) or self.text[self.pos] != "'":
            raise RegexParseError("Expected single-quoted character", self.pos)
        self.pos += 1
        if self.pos >= len(self.text):
            raise RegexParseError("Unterminated character literal", self.pos)
        if self.text[self.pos] == "\\":
            ch = self._parse_escape()
        else:
            ch = ord(self.text[self.pos])
            self.pos += 1
        if self.pos < len(self.text) and self.text[self.pos] == "'":
            self.pos += 1
        return ReLiteral(ch)

    def _parse_string_literal(self) -> RegexNode:
        if self.pos >= len(self.text) or self.text[self.pos] != '"':
            raise RegexParseError('Expected double-quoted string', self.pos)
        self.pos += 1
        chars: list[int] = []
        while self.pos < len(self.text) and self.text[self.pos] != '"':
            if self.text[self.pos] == "\\":
                chars.append(self._parse_escape())
            else:
                chars.append(ord(self.text[self.pos]))
                self.pos += 1
        if self.pos < len(self.text):
            self.pos += 1
        if not chars:
            raise RegexParseError("Empty string literal", self.pos)
        node: RegexNode = ReLiteral(chars[0])
        for c in chars[1:]:
            node = ReConcat(node, ReLiteral(c))
        return node

    def _parse_escape(self) -> int:
        if self.pos >= len(self.text) or self.text[self.pos] != "\\":
            raise RegexParseError("Expected escape sequence", self.pos)
        self.pos += 1
        if self.pos >= len(self.text):
            raise RegexParseError("Unterminated escape", self.pos)
        ch = self.text[self.pos]
        self.pos += 1
        escape_map = {
            "n": 10,
            "t": 9,
            "r": 13,
            "\\": 92,
            "'": 39,
            '"': 34,
            "0": 0,
            "s": 32,
            "a": 7,
            "b": 8,
            "f": 12,
            "v": 11,
        }
        if ch in escape_map:
            return escape_map[ch]
        return ord(ch)

    def _parse_charclass(self) -> ReCharClass:
        if self.pos >= len(self.text) or self.text[self.pos] != "[":
            raise RegexParseError("Expected '[' to start character class", self.pos)
        self.pos += 1
        negated = False
        if self.pos < len(self.text) and self.text[self.pos] == "^":
            negated = True
            self.pos += 1

        chars: set[int] = set()
        while self.pos < len(self.text) and self.text[self.pos] != "]":
            self._skip_ws()
            if self.pos < len(self.text) and self.text[self.pos] == "]":
                break

            if self.text[self.pos] == '"':
                self.pos += 1
                while self.pos < len(self.text) and self.text[self.pos] != '"':
                    if self.text[self.pos] == "\\":
                        chars.add(self._parse_escape())
                    else:
                        chars.add(ord(self.text[self.pos]))
                        self.pos += 1
                if self.pos < len(self.text):
                    self.pos += 1
            elif self.text[self.pos] == "'":
                c1 = self._parse_char_literal_value()
                self._skip_ws()
                if self.pos < len(self.text) and self.text[self.pos] == "-":
                    self.pos += 1
                    self._skip_ws()
                    c2 = self._parse_char_literal_value()
                    for c in range(c1, c2 + 1):
                        chars.add(c)
                else:
                    chars.add(c1)
            else:
                chars.add(ord(self.text[self.pos]))
                self.pos += 1

        if self.pos < len(self.text) and self.text[self.pos] == "]":
            self.pos += 1
        return ReCharClass(chars, negated)

    def _parse_char_literal_value(self) -> int:
        if self.pos >= len(self.text) or self.text[self.pos] != "'":
            raise RegexParseError("Expected single-quoted character", self.pos)
        self.pos += 1
        if self.pos >= len(self.text):
            raise RegexParseError("Unterminated character literal", self.pos)
        if self.text[self.pos] == "\\":
            val = self._parse_escape()
        else:
            val = ord(self.text[self.pos])
            self.pos += 1
        if self.pos < len(self.text) and self.text[self.pos] == "'":
            self.pos += 1
        return val
