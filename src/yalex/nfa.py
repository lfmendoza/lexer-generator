"""NFA construction (Thompson's algorithm)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from yalex.regex_ast import (
    ReAny,
    ReCharClass,
    ReConcat,
    ReDifference,
    ReEOF,
    RegexNode,
    ReLiteral,
    ReOptional,
    RePlus,
    ReStar,
    ReUnion,
)


@dataclass
class NFAState:
    id: int
    transitions: dict[int | None, list[int]] = field(default_factory=lambda: defaultdict(list))
    is_accept: bool = False
    rule_index: int = -1


@dataclass
class NFA:
    start: int
    accept: int
    states: dict[int, NFAState]


class NFABuilder:
    def __init__(self) -> None:
        self._next_id = 0

    def new_state(self) -> NFAState:
        """Create a new NFA state (public API for pipeline composition)."""
        s = NFAState(self._next_id)
        self._next_id += 1
        return s

    def build(self, node: RegexNode, rule_index: int = -1) -> NFA:
        """Build an NFA from a regex AST node."""
        nfa = self._build_node(node)
        if rule_index >= 0:
            nfa.states[nfa.accept].is_accept = True
            nfa.states[nfa.accept].rule_index = rule_index
        return nfa

    def _build_node(self, node: RegexNode) -> NFA:
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
        s0 = self.new_state()
        s1 = self.new_state()
        s0.transitions[ch].append(s1.id)
        states = {s0.id: s0, s1.id: s1}
        return NFA(s0.id, s1.id, states)

    def _build_charclass(self, node: ReCharClass) -> NFA:
        chars = node.effective_chars()
        s0 = self.new_state()
        s1 = self.new_state()
        for ch in chars:
            s0.transitions[ch].append(s1.id)
        states = {s0.id: s0, s1.id: s1}
        return NFA(s0.id, s1.id, states)

    def _build_any(self) -> NFA:
        s0 = self.new_state()
        s1 = self.new_state()
        for ch in range(1, 128):
            s0.transitions[ch].append(s1.id)
        states = {s0.id: s0, s1.id: s1}
        return NFA(s0.id, s1.id, states)

    def _build_eof(self) -> NFA:
        s0 = self.new_state()
        s1 = self.new_state()
        s0.transitions[-1].append(s1.id)
        states = {s0.id: s0, s1.id: s1}
        return NFA(s0.id, s1.id, states)

    def _build_concat(self, node: ReConcat) -> NFA:
        left = self._build_node(node.left)
        right = self._build_node(node.right)
        left.states[left.accept].transitions[None].append(right.start)
        states = {**left.states, **right.states}
        return NFA(left.start, right.accept, states)

    def _build_union(self, node: ReUnion) -> NFA:
        left = self._build_node(node.left)
        right = self._build_node(node.right)
        s0 = self.new_state()
        s1 = self.new_state()
        s0.transitions[None].append(left.start)
        s0.transitions[None].append(right.start)
        left.states[left.accept].transitions[None].append(s1.id)
        right.states[right.accept].transitions[None].append(s1.id)
        states = {s0.id: s0, s1.id: s1, **left.states, **right.states}
        return NFA(s0.id, s1.id, states)

    def _build_star(self, node: ReStar) -> NFA:
        child = self._build_node(node.child)
        s0 = self.new_state()
        s1 = self.new_state()
        s0.transitions[None].append(child.start)
        s0.transitions[None].append(s1.id)
        child.states[child.accept].transitions[None].append(child.start)
        child.states[child.accept].transitions[None].append(s1.id)
        states = {s0.id: s0, s1.id: s1, **child.states}
        return NFA(s0.id, s1.id, states)

    def _build_plus(self, node: RePlus) -> NFA:
        child = self._build_node(node.child)
        s0 = self.new_state()
        s1 = self.new_state()
        s0.transitions[None].append(child.start)
        child.states[child.accept].transitions[None].append(child.start)
        child.states[child.accept].transitions[None].append(s1.id)
        states = {s0.id: s0, s1.id: s1, **child.states}
        return NFA(s0.id, s1.id, states)

    def _build_optional(self, node: ReOptional) -> NFA:
        child = self._build_node(node.child)
        s0 = self.new_state()
        s1 = self.new_state()
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

    def _resolve_charset_from_node(self, node: RegexNode) -> set[int]:
        if isinstance(node, ReCharClass):
            return node.effective_chars()
        elif isinstance(node, ReLiteral):
            return {node.char}
        elif isinstance(node, ReAny):
            return set(range(0, 128))
        raise ValueError(f"Cannot resolve charset from {type(node)}")
