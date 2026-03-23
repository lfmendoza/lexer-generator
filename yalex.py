#!/usr/bin/env python3
"""
YALex - Yet Another Lex
Lexer Generator: reads a .yal specification and produces a Python lexer.

Usage:
    python yalex.py lexer.yal -o thelexer

Modules:
    1. YALex Parser        – parses .yal file structure
    2. Regex Parser        – parses YALex regex syntax into an AST
    3. NFA Builder         – Thompson's construction
    4. DFA Builder         – subset construction + minimization
    5. Code Generator      – emits a standalone Python lexer
    6. Tree Visualizer     – renders the expression tree with graphviz
"""

import sys
import os
import argparse
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set, FrozenSet
from collections import defaultdict, deque

# ═══════════════════════════════════════════════════════════════════════════════
#  1. DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

# --- Regex AST Nodes ---

@dataclass
class ReLiteral:
    """Single character."""
    char: int  # ordinal

@dataclass
class ReCharClass:
    """Set of characters (possibly negated)."""
    chars: Set[int]
    negated: bool = False

    def effective_chars(self) -> Set[int]:
        if self.negated:
            return set(range(0, 128)) - self.chars
        return set(self.chars)

@dataclass
class ReConcat:
    left: object
    right: object

@dataclass
class ReUnion:
    left: object
    right: object

@dataclass
class ReStar:
    child: object

@dataclass
class RePlus:
    child: object

@dataclass
class ReOptional:
    child: object

@dataclass
class ReDifference:
    """Set difference: left # right (both must be char classes)."""
    left: object
    right: object

@dataclass
class ReAny:
    """Wildcard _ : matches any character."""
    pass

@dataclass
class ReEOF:
    """Special EOF marker."""
    pass

# End-marker for direct DFA construction
@dataclass
class ReEndMarker:
    rule_index: int

# --- NFA ---

@dataclass
class NFAState:
    id: int
    transitions: Dict[Optional[int], List[int]] = field(default_factory=lambda: defaultdict(list))
    # None key = epsilon
    is_accept: bool = False
    rule_index: int = -1  # which rule this accept state belongs to

@dataclass
class NFA:
    start: int
    accept: int
    states: Dict[int, NFAState]

# --- DFA ---

@dataclass
class DFAState:
    id: int
    transitions: Dict[int, int] = field(default_factory=dict)
    is_accept: bool = False
    rule_index: int = -1  # lowest (highest priority) rule index among accept states

# ═══════════════════════════════════════════════════════════════════════════════
#  2. YALEX FILE PARSER
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class YALexRule:
    pattern_str: str
    action: str  # code inside { }

@dataclass
class YALexSpec:
    header: str
    trailer: str
    definitions: List[Tuple[str, str]]  # (name, regex_str)
    entrypoint: str
    rules: List[YALexRule]


def parse_yalex_file(filepath: str) -> YALexSpec:
    """Parse a .yal file into a YALexSpec."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove comments (* ... *)
    content = _remove_comments(content)

    header = ""
    trailer = ""
    definitions = []
    entrypoint = "tokens"
    rules = []

    pos = 0
    length = len(content)

    def skip_ws():
        nonlocal pos
        while pos < length and content[pos] in ' \t\r\n':
            pos += 1

    # --- Try to parse header { ... } ---
    skip_ws()
    if pos < length and content[pos] == '{':
        header, pos = _extract_braces(content, pos)

    # --- Parse let definitions ---
    skip_ws()
    while pos < length:
        skip_ws()
        if content[pos:pos+3] == 'let':
            pos += 3
            skip_ws()
            # read ident
            ident_start = pos
            while pos < length and (content[pos].isalnum() or content[pos] == '_'):
                pos += 1
            ident = content[ident_start:pos]
            skip_ws()
            assert content[pos] == '=', f"Expected '=' after let {ident}, got '{content[pos]}' at pos {pos}"
            pos += 1
            skip_ws()
            # read regex until newline (but handle brackets, quotes, etc.)
            regex_str, pos = _read_let_regex(content, pos)
            definitions.append((ident, regex_str.strip()))
        elif content[pos:pos+4] == 'rule':
            break
        else:
            pos += 1

    # --- Parse rule section ---
    skip_ws()
    if content[pos:pos+4] == 'rule':
        pos += 4
        skip_ws()
        # read entrypoint name
        ep_start = pos
        while pos < length and (content[pos].isalnum() or content[pos] == '_'):
            pos += 1
        entrypoint = content[ep_start:pos]
        skip_ws()
        # skip optional arguments and '='
        while pos < length and content[pos] != '=':
            pos += 1
        pos += 1  # skip '='
        skip_ws()

        # Parse rules:  pattern { action } | pattern { action } ...
        rules = _parse_rules(content, pos)
        # Find where rules end to check for trailer
        last_rule_end = _find_rules_end(content, pos)
        pos = last_rule_end

    # --- Try to parse trailer { ... } ---
    skip_ws()
    if pos < length and content[pos] == '{':
        trailer, pos = _extract_braces(content, pos)

    return YALexSpec(header, trailer, definitions, entrypoint, rules)


def _remove_comments(text: str) -> str:
    """Remove (* ... *) comments, handling nesting."""
    result = []
    i = 0
    while i < len(text):
        if i + 1 < len(text) and text[i] == '(' and text[i+1] == '*':
            depth = 1
            i += 2
            while i < len(text) and depth > 0:
                if i + 1 < len(text) and text[i] == '(' and text[i+1] == '*':
                    depth += 1
                    i += 2
                elif i + 1 < len(text) and text[i] == '*' and text[i+1] == ')':
                    depth -= 1
                    i += 2
                else:
                    i += 1
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


def _extract_braces(text: str, pos: int) -> Tuple[str, int]:
    """Extract content between { and }, handling nesting. Returns (content, new_pos)."""
    assert text[pos] == '{'
    depth = 1
    start = pos + 1
    pos += 1
    while pos < len(text) and depth > 0:
        if text[pos] == '{':
            depth += 1
        elif text[pos] == '}':
            depth -= 1
        pos += 1
    return text[start:pos-1].strip(), pos


def _read_let_regex(text: str, pos: int) -> Tuple[str, int]:
    """Read a regex from a let definition until unambiguous end (next 'let', 'rule', or '{' at top level)."""
    start = pos
    length = len(text)
    while pos < length:
        # Check for next keyword at start of logical line
        rest = text[pos:].lstrip()
        if rest.startswith('let ') or rest.startswith('rule '):
            break
        # Read the whole line
        while pos < length and text[pos] != '\n':
            if text[pos] == '\'' :
                pos += 1
                while pos < length and text[pos] != '\'':
                    if text[pos] == '\\':
                        pos += 1
                    pos += 1
                pos += 1  # skip closing '
            elif text[pos] == '"':
                pos += 1
                while pos < length and text[pos] != '"':
                    if text[pos] == '\\':
                        pos += 1
                    pos += 1
                pos += 1
            elif text[pos] == '[':
                while pos < length and text[pos] != ']':
                    pos += 1
                pos += 1
            else:
                pos += 1
        if pos < length:
            pos += 1  # skip \n
    return text[start:pos], pos


def _parse_rules(text: str, pos: int) -> List[YALexRule]:
    """Parse rule alternatives: pattern { action } | pattern { action } ..."""
    rules = []
    length = len(text)

    def skip_ws():
        nonlocal pos
        while pos < length and text[pos] in ' \t\r\n':
            pos += 1

    while pos < length:
        skip_ws()
        if pos >= length:
            break

        # Check for trailer
        # A '{' that starts a trailer vs an action: trailer { appears after all rules end.
        # We detect end of rules when we see '{' without a preceding pattern.

        # Skip leading '|'
        if text[pos] == '|':
            pos += 1
            skip_ws()

        if pos >= length:
            break

        # Check if this looks like a trailer (bare '{' at start without a pattern)
        # Heuristic: if we already have rules and see '{' without pattern chars before it, it's trailer
        if text[pos] == '{' and rules:
            # Peek: is there a valid pattern before this brace? No — it's likely trailer
            break

        # Read pattern
        pattern, pos = _read_rule_pattern(text, pos)
        if not pattern.strip():
            break

        skip_ws()

        # Read action (if present)
        action = ""
        if pos < length and text[pos] == '{':
            action, pos = _extract_braces(text, pos)

        rules.append(YALexRule(pattern.strip(), action.strip()))

    return rules


def _read_rule_pattern(text: str, pos: int) -> Tuple[str, int]:
    """Read a rule pattern until we hit '{' (action) or '|' at top level."""
    start = pos
    length = len(text)
    depth_bracket = 0
    depth_paren = 0

    while pos < length:
        ch = text[pos]
        if ch == '\'':
            pos += 1
            while pos < length and text[pos] != '\'':
                if text[pos] == '\\':
                    pos += 1
                pos += 1
            pos += 1
        elif ch == '"':
            pos += 1
            while pos < length and text[pos] != '"':
                if text[pos] == '\\':
                    pos += 1
                pos += 1
            pos += 1
        elif ch == '[':
            depth_bracket += 1
            pos += 1
        elif ch == ']':
            depth_bracket -= 1
            pos += 1
        elif ch == '(':
            depth_paren += 1
            pos += 1
        elif ch == ')':
            depth_paren -= 1
            pos += 1
        elif ch == '{' and depth_bracket == 0 and depth_paren == 0:
            break
        elif ch == '|' and depth_bracket == 0 and depth_paren == 0:
            break
        else:
            pos += 1

    return text[start:pos], pos


def _find_rules_end(text: str, pos: int) -> int:
    """Find the position after all rules have been parsed."""
    length = len(text)
    last_action_end = pos
    while pos < length:
        if text[pos] == '{':
            depth = 1
            pos += 1
            while pos < length and depth > 0:
                if text[pos] == '{': depth += 1
                elif text[pos] == '}': depth -= 1
                pos += 1
            last_action_end = pos
        elif text[pos] in ' \t\r\n':
            pos += 1
        elif text[pos] == '|':
            pos += 1
        else:
            # Could be start of trailer or more pattern
            # Simple heuristic: scan forward
            # Look for 'let' or 'rule' keywords or another '{'
            line_start = pos
            while pos < length and text[pos] not in '{|\n':
                pos += 1
            if pos < length and text[pos] == '{':
                # Check if it looks like a pattern+action or a trailer
                segment = text[line_start:pos].strip()
                if not segment:
                    # bare '{' — trailer
                    return line_start
                # else continue (it's a pattern)
                continue
            elif pos < length and text[pos] == '|':
                continue
            elif pos < length and text[pos] == '\n':
                pos += 1
                continue
            else:
                break
    return last_action_end


# ═══════════════════════════════════════════════════════════════════════════════
#  3. REGEX PARSER (YALex regex syntax → AST)
# ═══════════════════════════════════════════════════════════════════════════════

class RegexParser:
    """
    Parses YALex regex syntax into AST nodes.
    
    Precedence (low to high):
        |  (union)
        concat
        * + ?
        # (set difference)
    
    Grammar:
        expr     -> concat ('|' concat)*
        concat   -> unary (unary)*
        unary    -> primary ('*' | '+' | '?')*
        primary  -> charclass | '(' expr ')' | literal | string | ident | '_' | 'eof'
        charclass-> '[' '^'? (char '-' char | char | string)* ']'
        primary  -> primary '#' primary   (handled at unary level with higher prec)
    
    Adjusted for # having highest precedence:
        expr     -> concat ('|' concat)*
        concat   -> unary (unary)*
        unary    -> diff ('*' | '+' | '?')*
        diff     -> primary ('#' primary)*
        primary  -> charclass | '(' expr ')' | literal | string | ident | '_' | 'eof'
    """

    def __init__(self, text: str, definitions: Dict[str, str]):
        self.text = text
        self.pos = 0
        self.definitions = definitions  # name -> regex_str (already parsed or raw)
        self.parsed_defs: Dict[str, object] = {}  # cache

    def parse(self) -> object:
        node = self._expr()
        return node

    def _peek(self) -> Optional[str]:
        self._skip_ws()
        if self.pos < len(self.text):
            return self.text[self.pos]
        return None

    def _skip_ws(self):
        while self.pos < len(self.text) and self.text[self.pos] in ' \t':
            self.pos += 1

    def _expr(self) -> object:
        """expr -> concat ('|' concat)*"""
        left = self._concat()
        while self._peek() == '|':
            self.pos += 1
            right = self._concat()
            left = ReUnion(left, right)
        return left

    def _concat(self) -> object:
        """concat -> unary (unary)*"""
        node = self._unary()
        while True:
            p = self._peek()
            if p is None or p in '|)':
                break
            # Next token must be a valid start of a unary expression
            if p in '([\'\"_' or (p.isalnum() and p != '|') or p == '[':
                right = self._unary()
                node = ReConcat(node, right)
            else:
                break
        return node

    def _unary(self) -> object:
        """unary -> diff ('*' | '+' | '?')*"""
        node = self._diff()
        while self._peek() in ('*', '+', '?'):
            op = self.text[self.pos]
            self.pos += 1
            if op == '*':
                node = ReStar(node)
            elif op == '+':
                node = RePlus(node)
            elif op == '?':
                node = ReOptional(node)
        return node

    def _diff(self) -> object:
        """diff -> primary ('#' primary)*"""
        node = self._primary()
        while self._peek() == '#':
            self.pos += 1
            right = self._primary()
            # Resolve to char class difference
            left_chars = self._resolve_charset(node)
            right_chars = self._resolve_charset(right)
            diff_chars = left_chars - right_chars
            node = ReCharClass(diff_chars)
        return node

    def _resolve_charset(self, node) -> Set[int]:
        """Resolve a node to a set of character ordinals."""
        if isinstance(node, ReCharClass):
            return node.effective_chars()
        elif isinstance(node, ReLiteral):
            return {node.char}
        elif isinstance(node, ReAny):
            return set(range(0, 128))
        else:
            raise ValueError(f"Cannot resolve charset from {type(node).__name__}")

    def _primary(self) -> object:
        """primary -> charclass | '(' expr ')' | literal | string | ident | '_' | 'eof'"""
        self._skip_ws()
        if self.pos >= len(self.text):
            raise ValueError("Unexpected end of regex")

        ch = self.text[self.pos]

        # Character class [...]
        if ch == '[':
            return self._parse_charclass()

        # Grouped expression
        if ch == '(':
            self.pos += 1
            node = self._expr()
            self._skip_ws()
            if self.pos < len(self.text) and self.text[self.pos] == ')':
                self.pos += 1
            return node

        # Single-quoted literal
        if ch == '\'':
            return self._parse_char_literal()

        # Double-quoted string
        if ch == '"':
            return self._parse_string_literal()

        # Wildcard
        if ch == '_' and (self.pos + 1 >= len(self.text) or not self.text[self.pos + 1].isalnum()):
            self.pos += 1
            return ReAny()

        # Identifier or 'eof'
        if ch.isalpha() or ch == '_':
            ident = self._read_ident()
            if ident == 'eof':
                return ReEOF()
            # Look up definition
            if ident in self.definitions:
                if ident not in self.parsed_defs:
                    sub_parser = RegexParser(self.definitions[ident], self.definitions)
                    sub_parser.parsed_defs = self.parsed_defs
                    self.parsed_defs[ident] = sub_parser.parse()
                return self.parsed_defs[ident]
            raise ValueError(f"Undefined identifier: {ident}")

        raise ValueError(f"Unexpected character '{ch}' at position {self.pos} in regex: {self.text}")

    def _read_ident(self) -> str:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        return self.text[start:self.pos]

    def _parse_char_literal(self) -> ReLiteral:
        """Parse 'c' or '\n' etc."""
        assert self.text[self.pos] == '\''
        self.pos += 1
        if self.text[self.pos] == '\\':
            ch = self._parse_escape()
        else:
            ch = ord(self.text[self.pos])
            self.pos += 1
        if self.pos < len(self.text) and self.text[self.pos] == '\'':
            self.pos += 1
        return ReLiteral(ch)

    def _parse_string_literal(self) -> object:
        """Parse "abc" as concatenation of literals."""
        assert self.text[self.pos] == '"'
        self.pos += 1
        chars = []
        while self.pos < len(self.text) and self.text[self.pos] != '"':
            if self.text[self.pos] == '\\':
                chars.append(self._parse_escape())
            else:
                chars.append(ord(self.text[self.pos]))
                self.pos += 1
        if self.pos < len(self.text):
            self.pos += 1  # skip closing "
        if not chars:
            raise ValueError("Empty string literal")
        node = ReLiteral(chars[0])
        for c in chars[1:]:
            node = ReConcat(node, ReLiteral(c))
        return node

    def _parse_escape(self) -> int:
        """Parse an escape sequence, return ordinal."""
        assert self.text[self.pos] == '\\'
        self.pos += 1
        ch = self.text[self.pos]
        self.pos += 1
        escape_map = {
            'n': 10, 't': 9, 'r': 13, '\\': 92,
            '\'': 39, '"': 34, '0': 0,
            's': 32, 'a': 7, 'b': 8, 'f': 12, 'v': 11,
        }
        if ch in escape_map:
            return escape_map[ch]
        return ord(ch)

    def _parse_charclass(self) -> ReCharClass:
        """Parse [charset] or [^charset]."""
        assert self.text[self.pos] == '['
        self.pos += 1
        negated = False
        if self.pos < len(self.text) and self.text[self.pos] == '^':
            negated = True
            self.pos += 1

        chars: Set[int] = set()
        while self.pos < len(self.text) and self.text[self.pos] != ']':
            self._skip_ws()
            if self.pos < len(self.text) and self.text[self.pos] == ']':
                break

            if self.text[self.pos] == '"':
                # String inside charset: "abcd" -> {a, b, c, d}
                self.pos += 1
                while self.pos < len(self.text) and self.text[self.pos] != '"':
                    if self.text[self.pos] == '\\':
                        chars.add(self._parse_escape())
                    else:
                        chars.add(ord(self.text[self.pos]))
                        self.pos += 1
                if self.pos < len(self.text):
                    self.pos += 1  # skip "
            elif self.text[self.pos] == '\'':
                # Character literal inside charset, possibly part of a range
                c1 = self._parse_char_literal_value()
                self._skip_ws()
                if self.pos < len(self.text) and self.text[self.pos] == '-':
                    self.pos += 1
                    self._skip_ws()
                    c2 = self._parse_char_literal_value()
                    for c in range(c1, c2 + 1):
                        chars.add(c)
                else:
                    chars.add(c1)
            else:
                # bare character
                chars.add(ord(self.text[self.pos]))
                self.pos += 1

        if self.pos < len(self.text) and self.text[self.pos] == ']':
            self.pos += 1
        return ReCharClass(chars, negated)

    def _parse_char_literal_value(self) -> int:
        """Parse 'c' and return ordinal."""
        assert self.text[self.pos] == '\''
        self.pos += 1
        if self.text[self.pos] == '\\':
            val = self._parse_escape()
        else:
            val = ord(self.text[self.pos])
            self.pos += 1
        if self.pos < len(self.text) and self.text[self.pos] == '\'':
            self.pos += 1
        return val


# ═══════════════════════════════════════════════════════════════════════════════
#  4. NFA CONSTRUCTION (Thompson's)
# ═══════════════════════════════════════════════════════════════════════════════

class NFABuilder:
    def __init__(self):
        self._next_id = 0

    def _new_state(self) -> NFAState:
        s = NFAState(self._next_id)
        self._next_id += 1
        return s

    def build(self, node, rule_index: int = -1) -> NFA:
        """Build an NFA from a regex AST node."""
        nfa = self._build_node(node)
        if rule_index >= 0:
            nfa.states[nfa.accept].is_accept = True
            nfa.states[nfa.accept].rule_index = rule_index
        return nfa

    def _build_node(self, node) -> NFA:
        if isinstance(node, ReLiteral):
            return self._build_literal(node.char)
        elif isinstance(node, ReCharClass):
            return self._build_charclass(node)
        elif isinstance(node, ReAny):
            return self._build_any()
        elif isinstance(node, ReConcat):
            return self._build_concat(node)
        elif isinstance(node, ReUnion):
            return self._build_union(node)
        elif isinstance(node, ReStar):
            return self._build_star(node)
        elif isinstance(node, RePlus):
            return self._build_plus(node)
        elif isinstance(node, ReOptional):
            return self._build_optional(node)
        elif isinstance(node, ReDifference):
            return self._build_diff(node)
        elif isinstance(node, ReEOF):
            return self._build_eof()
        else:
            raise ValueError(f"Unknown AST node: {type(node)}")

    def _build_literal(self, ch: int) -> NFA:
        s0 = self._new_state()
        s1 = self._new_state()
        s0.transitions[ch].append(s1.id)
        states = {s0.id: s0, s1.id: s1}
        return NFA(s0.id, s1.id, states)

    def _build_charclass(self, node: ReCharClass) -> NFA:
        chars = node.effective_chars()
        s0 = self._new_state()
        s1 = self._new_state()
        for ch in chars:
            s0.transitions[ch].append(s1.id)
        states = {s0.id: s0, s1.id: s1}
        return NFA(s0.id, s1.id, states)

    def _build_any(self) -> NFA:
        s0 = self._new_state()
        s1 = self._new_state()
        for ch in range(1, 128):  # all printable + control except NUL
            s0.transitions[ch].append(s1.id)
        states = {s0.id: s0, s1.id: s1}
        return NFA(s0.id, s1.id, states)

    def _build_eof(self) -> NFA:
        # EOF represented by special value -1
        s0 = self._new_state()
        s1 = self._new_state()
        s0.transitions[-1].append(s1.id)
        states = {s0.id: s0, s1.id: s1}
        return NFA(s0.id, s1.id, states)

    def _build_concat(self, node: ReConcat) -> NFA:
        left = self._build_node(node.left)
        right = self._build_node(node.right)
        # Connect left accept to right start via epsilon
        left.states[left.accept].transitions[None].append(right.start)
        states = {**left.states, **right.states}
        return NFA(left.start, right.accept, states)

    def _build_union(self, node: ReUnion) -> NFA:
        left = self._build_node(node.left)
        right = self._build_node(node.right)
        s0 = self._new_state()
        s1 = self._new_state()
        s0.transitions[None].append(left.start)
        s0.transitions[None].append(right.start)
        left.states[left.accept].transitions[None].append(s1.id)
        right.states[right.accept].transitions[None].append(s1.id)
        states = {s0.id: s0, s1.id: s1, **left.states, **right.states}
        return NFA(s0.id, s1.id, states)

    def _build_star(self, node: ReStar) -> NFA:
        child = self._build_node(node.child)
        s0 = self._new_state()
        s1 = self._new_state()
        s0.transitions[None].append(child.start)
        s0.transitions[None].append(s1.id)
        child.states[child.accept].transitions[None].append(child.start)
        child.states[child.accept].transitions[None].append(s1.id)
        states = {s0.id: s0, s1.id: s1, **child.states}
        return NFA(s0.id, s1.id, states)

    def _build_plus(self, node: RePlus) -> NFA:
        child = self._build_node(node.child)
        s0 = self._new_state()
        s1 = self._new_state()
        s0.transitions[None].append(child.start)
        child.states[child.accept].transitions[None].append(child.start)
        child.states[child.accept].transitions[None].append(s1.id)
        states = {s0.id: s0, s1.id: s1, **child.states}
        return NFA(s0.id, s1.id, states)

    def _build_optional(self, node: ReOptional) -> NFA:
        child = self._build_node(node.child)
        s0 = self._new_state()
        s1 = self._new_state()
        s0.transitions[None].append(child.start)
        s0.transitions[None].append(s1.id)
        child.states[child.accept].transitions[None].append(s1.id)
        states = {s0.id: s0, s1.id: s1, **child.states}
        return NFA(s0.id, s1.id, states)

    def _build_diff(self, node: ReDifference) -> NFA:
        left_chars = self._resolve_charset_from_node(node.left)
        right_chars = self._resolve_charset_from_node(node.right)
        diff = left_chars - right_chars
        return self._build_charclass(ReCharClass(diff))

    def _resolve_charset_from_node(self, node) -> Set[int]:
        if isinstance(node, ReCharClass):
            return node.effective_chars()
        elif isinstance(node, ReLiteral):
            return {node.char}
        elif isinstance(node, ReAny):
            return set(range(0, 128))
        raise ValueError(f"Cannot resolve charset from {type(node)}")


# ═══════════════════════════════════════════════════════════════════════════════
#  5. DFA CONSTRUCTION (Subset Construction)
# ═══════════════════════════════════════════════════════════════════════════════

def epsilon_closure(nfa_states: Dict[int, NFAState], state_set: FrozenSet[int]) -> FrozenSet[int]:
    """Compute epsilon closure of a set of NFA states."""
    stack = list(state_set)
    closure = set(state_set)
    while stack:
        s = stack.pop()
        for t in nfa_states[s].transitions.get(None, []):
            if t not in closure:
                closure.add(t)
                stack.append(t)
    return frozenset(closure)


def move(nfa_states: Dict[int, NFAState], state_set: FrozenSet[int], symbol: int) -> FrozenSet[int]:
    """Compute the set of states reachable from state_set on symbol."""
    result = set()
    for s in state_set:
        for t in nfa_states[s].transitions.get(symbol, []):
            result.add(t)
    return frozenset(result)


def nfa_to_dfa(nfa: NFA) -> Tuple[Dict[int, DFAState], int]:
    """Subset construction: NFA -> DFA. Returns (states_dict, start_id)."""
    # Collect all symbols used in NFA transitions
    all_symbols: Set[int] = set()
    for state in nfa.states.values():
        for sym in state.transitions:
            if sym is not None:
                all_symbols.add(sym)

    start_closure = epsilon_closure(nfa.states, frozenset([nfa.start]))

    dfa_states: Dict[int, DFAState] = {}
    state_map: Dict[FrozenSet[int], int] = {}
    next_id = 0
    queue = deque()

    def get_or_create(nfa_set: FrozenSet[int]) -> int:
        nonlocal next_id
        if nfa_set in state_map:
            return state_map[nfa_set]
        sid = next_id
        next_id += 1
        state_map[nfa_set] = sid

        # Check accept status: pick lowest rule_index among accept states
        is_accept = False
        best_rule = -1
        for ns in nfa_set:
            ns_state = nfa.states[ns]
            if ns_state.is_accept:
                if not is_accept or ns_state.rule_index < best_rule:
                    best_rule = ns_state.rule_index
                is_accept = True

        dfa_states[sid] = DFAState(sid, {}, is_accept, best_rule)
        queue.append(nfa_set)
        return sid

    start_id = get_or_create(start_closure)

    while queue:
        current_nfa_set = queue.popleft()
        current_dfa_id = state_map[current_nfa_set]

        for sym in all_symbols:
            moved = move(nfa.states, current_nfa_set, sym)
            if not moved:
                continue
            closed = epsilon_closure(nfa.states, moved)
            if not closed:
                continue
            target_id = get_or_create(closed)
            dfa_states[current_dfa_id].transitions[sym] = target_id

    return dfa_states, start_id


# ═══════════════════════════════════════════════════════════════════════════════
#  6. DFA MINIMIZATION (Hopcroft-style partition refinement)
# ═══════════════════════════════════════════════════════════════════════════════

def minimize_dfa(dfa_states: Dict[int, DFAState], start_id: int) -> Tuple[Dict[int, DFAState], int]:
    """Minimize a DFA using partition refinement."""
    if not dfa_states:
        return dfa_states, start_id

    # Collect all symbols
    all_symbols: Set[int] = set()
    for s in dfa_states.values():
        all_symbols.update(s.transitions.keys())

    # Initial partition: group by (is_accept, rule_index)
    groups: Dict[Tuple[bool, int], Set[int]] = defaultdict(set)
    for sid, state in dfa_states.items():
        key = (state.is_accept, state.rule_index)
        groups[key].add(sid)

    partition = list(groups.values())

    def find_group(state_id: int) -> int:
        for i, group in enumerate(partition):
            if state_id in group:
                return i
        return -1

    changed = True
    while changed:
        changed = False
        new_partition = []
        for group in partition:
            if len(group) <= 1:
                new_partition.append(group)
                continue
            # Try to split
            splits: Dict[tuple, Set[int]] = defaultdict(set)
            for sid in group:
                sig = []
                for sym in sorted(all_symbols):
                    target = dfa_states[sid].transitions.get(sym, -1)
                    tg = find_group(target) if target != -1 else -1
                    sig.append(tg)
                splits[tuple(sig)].add(sid)
            if len(splits) > 1:
                changed = True
                new_partition.extend(splits.values())
            else:
                new_partition.append(group)
        partition = new_partition

    # Build new DFA
    group_of = {}
    for i, group in enumerate(partition):
        for sid in group:
            group_of[sid] = i

    new_states: Dict[int, DFAState] = {}
    for i, group in enumerate(partition):
        rep = next(iter(group))
        old_state = dfa_states[rep]
        new_trans = {}
        for sym, target in old_state.transitions.items():
            new_trans[sym] = group_of[target]
        new_states[i] = DFAState(i, new_trans, old_state.is_accept, old_state.rule_index)

    new_start = group_of[start_id]
    return new_states, new_start


# ═══════════════════════════════════════════════════════════════════════════════
#  7. COMBINED NFA/DFA FOR ALL RULES
# ═══════════════════════════════════════════════════════════════════════════════

def build_combined_dfa(spec: YALexSpec) -> Tuple[Dict[int, DFAState], int, List[str]]:
    """
    Build a single DFA that recognizes all rule patterns.
    Returns (dfa_states, start_id, actions_list).
    """
    definitions = dict(spec.definitions)
    builder = NFABuilder()

    # Build NFA for each rule and combine with a single start via epsilon
    super_start = builder._new_state()
    all_states = {super_start.id: super_start}
    actions = []

    for i, rule in enumerate(spec.rules):
        parser = RegexParser(rule.pattern_str, definitions)
        ast = parser.parse()
        nfa = builder.build(ast, rule_index=i)
        # Connect super_start to this NFA's start via epsilon
        super_start.transitions[None].append(nfa.start)
        all_states.update(nfa.states)
        actions.append(rule.action)

    # Find any accept state among all_states
    combined_accept = builder._new_state()  # dummy, won't be used as single accept
    all_states[combined_accept.id] = combined_accept

    combined_nfa = NFA(super_start.id, combined_accept.id, all_states)

    # Build DFA
    dfa_states, dfa_start = nfa_to_dfa(combined_nfa)

    # Minimize
    dfa_states, dfa_start = minimize_dfa(dfa_states, dfa_start)

    return dfa_states, dfa_start, actions


# ═══════════════════════════════════════════════════════════════════════════════
#  8. EXPRESSION TREE VISUALIZER (Graphviz DOT)
# ═══════════════════════════════════════════════════════════════════════════════

def ast_to_dot(node, name="expression_tree") -> str:
    """Generate Graphviz DOT representation of a regex AST."""
    lines = ["digraph {", f'  label="{name}";', '  node [shape=circle];']
    counter = [0]

    def _visit(n) -> int:
        nid = counter[0]
        counter[0] += 1

        if isinstance(n, ReLiteral):
            ch = chr(n.char) if 32 <= n.char < 127 else f"\\\\x{n.char:02x}"
            ch = ch.replace('"', '\\"').replace('\\', '\\\\') if ch not in ('\\\\',) else ch
            label = f"'{ch}'"
            lines.append(f'  n{nid} [label="{label}"];')
        elif isinstance(n, ReCharClass):
            label = "CharClass" if not n.negated else "^CharClass"
            lines.append(f'  n{nid} [label="{label}" shape=box];')
        elif isinstance(n, ReConcat):
            lines.append(f'  n{nid} [label="·"];')
            lid = _visit(n.left)
            rid = _visit(n.right)
            lines.append(f'  n{nid} -> n{lid};')
            lines.append(f'  n{nid} -> n{rid};')
        elif isinstance(n, ReUnion):
            lines.append(f'  n{nid} [label="|"];')
            lid = _visit(n.left)
            rid = _visit(n.right)
            lines.append(f'  n{nid} -> n{lid};')
            lines.append(f'  n{nid} -> n{rid};')
        elif isinstance(n, ReStar):
            lines.append(f'  n{nid} [label="*"];')
            cid = _visit(n.child)
            lines.append(f'  n{nid} -> n{cid};')
        elif isinstance(n, RePlus):
            lines.append(f'  n{nid} [label="+"];')
            cid = _visit(n.child)
            lines.append(f'  n{nid} -> n{cid};')
        elif isinstance(n, ReOptional):
            lines.append(f'  n{nid} [label="?"];')
            cid = _visit(n.child)
            lines.append(f'  n{nid} -> n{cid};')
        elif isinstance(n, ReAny):
            lines.append(f'  n{nid} [label="_" shape=diamond];')
        elif isinstance(n, ReEOF):
            lines.append(f'  n{nid} [label="EOF" shape=doublecircle];')
        elif isinstance(n, ReDifference):
            lines.append(f'  n{nid} [label="#"];')
            lid = _visit(n.left)
            rid = _visit(n.right)
            lines.append(f'  n{nid} -> n{lid};')
            lines.append(f'  n{nid} -> n{rid};')
        else:
            lines.append(f'  n{nid} [label="{type(n).__name__}"];')
        return nid

    _visit(node)
    lines.append("}")
    return "\n".join(lines)


def generate_all_trees(spec: YALexSpec, output_dir: str):
    """Generate DOT files for each rule's regex AST."""
    definitions = dict(spec.definitions)
    os.makedirs(output_dir, exist_ok=True)

    # Also generate trees for let definitions
    for name, regex_str in spec.definitions:
        parser = RegexParser(regex_str, definitions)
        ast = parser.parse()
        dot = ast_to_dot(ast, f"let {name}")
        dot_path = os.path.join(output_dir, f"def_{name}.dot")
        with open(dot_path, 'w') as f:
            f.write(dot)
        # Try to render with graphviz
        _try_render_dot(dot_path)

    for i, rule in enumerate(spec.rules):
        parser = RegexParser(rule.pattern_str, definitions)
        ast = parser.parse()
        dot = ast_to_dot(ast, f"rule_{i}")
        dot_path = os.path.join(output_dir, f"rule_{i}.dot")
        with open(dot_path, 'w') as f:
            f.write(dot)
        _try_render_dot(dot_path)

    # Combined tree (union of all rules)
    all_asts = []
    for rule in spec.rules:
        parser = RegexParser(rule.pattern_str, definitions)
        all_asts.append(parser.parse())
    if all_asts:
        combined = all_asts[0]
        for ast in all_asts[1:]:
            combined = ReUnion(combined, ast)
        dot = ast_to_dot(combined, "combined_rules")
        dot_path = os.path.join(output_dir, "combined.dot")
        with open(dot_path, 'w') as f:
            f.write(dot)
        _try_render_dot(dot_path)

    print(f"[INFO] Expression trees written to {output_dir}/")


def _try_render_dot(dot_path: str):
    """Try to render a DOT file to PNG using graphviz."""
    try:
        import subprocess
        png_path = dot_path.replace('.dot', '.png')
        subprocess.run(['dot', '-Tpng', dot_path, '-o', png_path],
                      capture_output=True, timeout=10)
    except Exception:
        pass  # graphviz not installed, skip


# ═══════════════════════════════════════════════════════════════════════════════
#  9. CODE GENERATOR (Python lexer)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_lexer(spec: YALexSpec, dfa_states: Dict[int, DFAState],
                   dfa_start: int, actions: List[str], output_path: str):
    """Generate a standalone Python lexer file."""

    # Serialize DFA transition table
    # Format: {state_id: {symbol: next_state, ...}, ...}
    trans_table = {}
    for sid, state in dfa_states.items():
        trans_table[sid] = dict(state.transitions)

    accept_table = {}
    for sid, state in dfa_states.items():
        if state.is_accept:
            accept_table[sid] = state.rule_index

    # Build action dispatch
    action_cases = []
    for i, action in enumerate(actions):
        if action:
            action_cases.append(f"        if rule_index == {i}:\n            {action}")
        else:
            action_cases.append(f"        if rule_index == {i}:\n            pass  # no action")

    action_dispatch = "\n".join(action_cases)

    code = f'''#!/usr/bin/env python3
"""
Auto-generated lexer by YALex.
Entry point: {spec.entrypoint}
"""

import sys

# --- Header ---
{spec.header}

# === DFA Tables ===
_TRANS_TABLE = {repr(trans_table)}

_ACCEPT_TABLE = {repr(accept_table)}

_START_STATE = {dfa_start}


class LexerError(Exception):
    def __init__(self, char, line, col):
        self.char = char
        self.line = line
        self.col = col
        super().__init__(f"Lexical error: unexpected character '{{char}}' at line {{line}}, column {{col}}")


class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []

    def {spec.entrypoint}(self):
        """Main lexer entry point. Returns list of tokens."""
        while self.pos < len(self.text):
            token = self._next_token()
            if token is not None:
                self.tokens.append(token)
        return self.tokens

    def _next_token(self):
        """Find the longest match from current position."""
        if self.pos >= len(self.text):
            return None

        state = _START_STATE
        last_accept_pos = -1
        last_accept_rule = -1
        current_pos = self.pos

        while current_pos <= len(self.text):
            # Check if current state is accepting
            if state in _ACCEPT_TABLE:
                last_accept_pos = current_pos
                last_accept_rule = _ACCEPT_TABLE[state]

            # Try to advance
            if current_pos >= len(self.text):
                # Check EOF transition (-1)
                trans = _TRANS_TABLE.get(state, {{}})
                if -1 in trans:
                    state = trans[-1]
                    current_pos += 1  # conceptual advance past EOF
                    if state in _ACCEPT_TABLE:
                        last_accept_pos = current_pos
                        last_accept_rule = _ACCEPT_TABLE[state]
                break

            ch = ord(self.text[current_pos])
            trans = _TRANS_TABLE.get(state, {{}})
            if ch in trans:
                state = trans[ch]
                current_pos += 1
            else:
                break

        if last_accept_rule >= 0 and last_accept_pos > self.pos:
            lexeme = self.text[self.pos:last_accept_pos]
            lxm = lexeme  # alias used in actions
            lexbuf = None  # placeholder

            # Update line/col tracking
            start_line = self.line
            start_col = self.col
            for ch in lexeme:
                if ch == '\\n':
                    self.line += 1
                    self.col = 1
                else:
                    self.col += 1

            self.pos = last_accept_pos
            rule_index = last_accept_rule

            # Execute action
            result = self._execute_action(rule_index, lexeme, lxm, start_line, start_col)
            return result
        elif last_accept_rule >= 0 and last_accept_pos == self.pos:
            # Zero-length match (e.g. optional), skip
            self.pos += 1
            return None
        else:
            # No match: lexical error
            bad_char = self.text[self.pos]
            err = LexerError(bad_char, self.line, self.col)
            print(f"ERROR: {{err}}", file=sys.stderr)
            # Skip the bad character and continue
            if bad_char == '\\n':
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            self.pos += 1
            return None

    def _execute_action(self, rule_index, lexeme, lxm, line, col):
        """Dispatch to the appropriate action for the matched rule."""
        lexbuf = self  # so actions can reference lexbuf
{action_dispatch}
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python {{sys.argv[0]}} <input_file>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        text = f.read()

    lexer = Lexer(text)
    tokens = lexer.{spec.entrypoint}()

    print("=== TOKENS ===")
    for tok in tokens:
        if tok is not None:
            print(tok)
    print(f"=== {{len([t for t in tokens if t is not None])}} tokens found ===")


if __name__ == "__main__":
    main()

# --- Trailer ---
{spec.trailer}
'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(code)

    print(f"[INFO] Lexer generated: {output_path}")


# ═══════════════════════════════════════════════════════════════════════════════
#  10. DFA VISUALIZATION (Graphviz DOT)
# ═══════════════════════════════════════════════════════════════════════════════

def dfa_to_dot(dfa_states: Dict[int, DFAState], start_id: int,
               actions: List[str], filename: str = "dfa"):
    """Generate Graphviz DOT for the DFA."""
    lines = [
        "digraph DFA {",
        "  rankdir=LR;",
        '  node [shape=circle];',
        f'  start [shape=point];',
        f'  start -> {start_id};',
    ]

    for sid, state in sorted(dfa_states.items()):
        if state.is_accept:
            action_label = actions[state.rule_index][:20] if state.rule_index < len(actions) else ""
            action_label = action_label.replace('"', '\\"').replace('\n', ' ')
            lines.append(f'  {sid} [shape=doublecircle label="{sid}\\n({action_label})"];')

        # Group transitions by target
        target_syms: Dict[int, List[int]] = defaultdict(list)
        for sym, target in state.transitions.items():
            target_syms[target].append(sym)

        for target, syms in target_syms.items():
            label = _format_symbol_set(syms)
            label = label.replace('"', '\\"')
            lines.append(f'  {sid} -> {target} [label="{label}"];')

    lines.append("}")

    dot_content = "\n".join(lines)
    dot_path = f"{filename}.dot"
    with open(dot_path, 'w') as f:
        f.write(dot_content)
    _try_render_dot(dot_path)
    print(f"[INFO] DFA diagram written to {dot_path}")


def _format_symbol_set(syms: List[int]) -> str:
    """Format a set of character codes into a readable label."""
    if len(syms) > 10:
        # Summarize
        ranges = _find_ranges(sorted(syms))
        parts = []
        for a, b in ranges:
            if a == b:
                parts.append(_char_label(a))
            else:
                parts.append(f"{_char_label(a)}-{_char_label(b)}")
        return ",".join(parts[:5]) + ("..." if len(parts) > 5 else "")
    return ",".join(_char_label(s) for s in sorted(syms))


def _char_label(ch: int) -> str:
    if ch == -1:
        return "EOF"
    if ch == ord('\n'):
        return "\\n"
    if ch == ord('\t'):
        return "\\t"
    if ch == ord(' '):
        return "SP"
    if 33 <= ch < 127:
        c = chr(ch)
        if c in '"\\':
            return f"\\{c}"
        return c
    return f"x{ch:02x}"


def _find_ranges(sorted_ints):
    if not sorted_ints:
        return []
    ranges = []
    start = sorted_ints[0]
    end = sorted_ints[0]
    for x in sorted_ints[1:]:
        if x == end + 1:
            end = x
        else:
            ranges.append((start, end))
            start = x
            end = x
    ranges.append((start, end))
    return ranges


# ═══════════════════════════════════════════════════════════════════════════════
#  11. MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="YALex - Yet Another Lex Generator")
    parser.add_argument("input", help="Input .yal file")
    parser.add_argument("-o", "--output", default=None, help="Output lexer filename (without extension)")
    parser.add_argument("--no-trees", action="store_true", help="Skip expression tree generation")
    parser.add_argument("--no-dfa-graph", action="store_true", help="Skip DFA graph generation")
    args = parser.parse_args()

    output_name = args.output or os.path.splitext(os.path.basename(args.input))[0] + "_lexer"
    output_path = output_name + ".py"
    tree_dir = output_name + "_trees"

    print(f"[YALex] Parsing {args.input}...")
    spec = parse_yalex_file(args.input)

    print(f"[YALex] Found {len(spec.definitions)} definitions, {len(spec.rules)} rules")
    print(f"[YALex] Entrypoint: {spec.entrypoint}")

    for name, regex_str in spec.definitions:
        print(f"  let {name} = {regex_str}")
    for i, rule in enumerate(spec.rules):
        action_preview = rule.action[:40] if rule.action else "(no action)"
        print(f"  rule {i}: {rule.pattern_str}  ->  {action_preview}")

    # Generate expression trees
    if not args.no_trees:
        print(f"\n[YALex] Generating expression trees...")
        generate_all_trees(spec, tree_dir)

    # Build combined DFA
    print(f"\n[YALex] Building NFA...")
    print(f"[YALex] Converting NFA -> DFA (subset construction)...")
    print(f"[YALex] Minimizing DFA...")
    dfa_states, dfa_start, actions = build_combined_dfa(spec)
    print(f"[YALex] DFA has {len(dfa_states)} states")

    # Generate DFA visualization
    if not args.no_dfa_graph:
        dfa_to_dot(dfa_states, dfa_start, actions, output_name + "_dfa")

    # Generate lexer
    print(f"\n[YALex] Generating lexer -> {output_path}")
    generate_lexer(spec, dfa_states, dfa_start, actions, output_path)

    print(f"\n[YALex] Done! Run your lexer with:")
    print(f"  python {output_path} <input_file>")


if __name__ == "__main__":
    main()