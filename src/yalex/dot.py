"""Graphviz DOT export for regex AST and DFA."""

from __future__ import annotations

import os
import subprocess
from collections import defaultdict

from yalex.dfa import DFAState
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
from yalex.regex_parser import RegexParser
from yalex.spec_parser import YALexSpec


def ast_to_dot(node: RegexNode, name: str = "expression_tree") -> str:
    """Generate Graphviz DOT representation of a regex AST."""
    lines = ["digraph {", f'  label="{name}";', "  node [shape=circle];"]
    counter = [0]

    def _visit(n: RegexNode) -> int:
        nid = counter[0]
        counter[0] += 1

        if isinstance(n, ReLiteral):
            ch = chr(n.char) if 32 <= n.char < 127 else f"\\\\x{n.char:02x}"
            ch = ch.replace('"', '\\"').replace("\\", "\\\\") if ch not in ("\\\\",) else ch
            label = f"'{ch}'"
            lines.append(f'  n{nid} [label="{label}"];')
        elif isinstance(n, ReCharClass):
            label = "CharClass" if not n.negated else "^CharClass"
            lines.append(f'  n{nid} [label="{label}" shape=box];')
        elif isinstance(n, ReConcat):
            lines.append(f'  n{nid} [label="·"];')
            lid = _visit(n.left)
            rid = _visit(n.right)
            lines.append(f"  n{nid} -> n{lid};")
            lines.append(f"  n{nid} -> n{rid};")
        elif isinstance(n, ReUnion):
            lines.append(f'  n{nid} [label="|"];')
            lid = _visit(n.left)
            rid = _visit(n.right)
            lines.append(f"  n{nid} -> n{lid};")
            lines.append(f"  n{nid} -> n{rid};")
        elif isinstance(n, ReStar):
            lines.append(f'  n{nid} [label="*"];')
            cid = _visit(n.child)
            lines.append(f"  n{nid} -> n{cid};")
        elif isinstance(n, RePlus):
            lines.append(f'  n{nid} [label="+"];')
            cid = _visit(n.child)
            lines.append(f"  n{nid} -> n{cid};")
        elif isinstance(n, ReOptional):
            lines.append(f'  n{nid} [label="?"];')
            cid = _visit(n.child)
            lines.append(f"  n{nid} -> n{cid};")
        elif isinstance(n, ReAny):
            lines.append(f'  n{nid} [label="_" shape=diamond];')
        elif isinstance(n, ReEOF):
            lines.append(f'  n{nid} [label="EOF" shape=doublecircle];')
        elif isinstance(n, ReDifference):
            lines.append(f'  n{nid} [label="#"];')
            lid = _visit(n.left)
            rid = _visit(n.right)
            lines.append(f"  n{nid} -> n{lid};")
            lines.append(f"  n{nid} -> n{rid};")
        else:
            lines.append(f'  n{nid} [label="{type(n).__name__}"];')
        return nid

    _visit(node)
    lines.append("}")
    return "\n".join(lines)


def generate_all_trees(spec: YALexSpec, output_dir: str, *, silent: bool = False) -> None:
    """Generate DOT files for each rule's regex AST."""
    definitions = dict(spec.definitions)
    os.makedirs(output_dir, exist_ok=True)

    for name, regex_str in spec.definitions:
        parser = RegexParser(regex_str, definitions)
        ast = parser.parse()
        dot = ast_to_dot(ast, f"let {name}")
        dot_path = os.path.join(output_dir, f"def_{name}.dot")
        with open(dot_path, "w", encoding="utf-8") as f:
            f.write(dot)
        _try_render_dot(dot_path)

    for i, rule in enumerate(spec.rules):
        parser = RegexParser(rule.pattern_str, definitions)
        ast = parser.parse()
        dot = ast_to_dot(ast, f"rule_{i}")
        dot_path = os.path.join(output_dir, f"rule_{i}.dot")
        with open(dot_path, "w", encoding="utf-8") as f:
            f.write(dot)
        _try_render_dot(dot_path)

    all_asts: list[RegexNode] = []
    for rule in spec.rules:
        parser = RegexParser(rule.pattern_str, definitions)
        all_asts.append(parser.parse())
    if all_asts:
        combined = all_asts[0]
        for ast in all_asts[1:]:
            combined = ReUnion(combined, ast)
        dot = ast_to_dot(combined, "combined_rules")
        dot_path = os.path.join(output_dir, "combined.dot")
        with open(dot_path, "w", encoding="utf-8") as f:
            f.write(dot)
        _try_render_dot(dot_path)

    if not silent:
        print(f"[INFO] Expression trees written to {output_dir}/")


def _try_render_dot(dot_path: str) -> None:
    try:
        png_path = dot_path.replace(".dot", ".png")
        subprocess.run(
            ["dot", "-Tpng", dot_path, "-o", png_path],
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        pass


def dfa_to_dot(
    dfa_states: dict[int, DFAState],
    start_id: int,
    actions: list[str],
    filename: str = "dfa",
    *,
    silent: bool = False,
) -> str:
    """Generate Graphviz DOT for the DFA. Returns path to .dot file written."""
    lines = [
        "digraph DFA {",
        "  rankdir=LR;",
        "  node [shape=circle];",
        "  start [shape=point];",
        f"  start -> {start_id};",
    ]

    for sid, state in sorted(dfa_states.items()):
        if state.is_accept:
            action_label = (
                actions[state.rule_index][:20] if state.rule_index < len(actions) else ""
            )
            action_label = action_label.replace('"', '\\"').replace("\n", " ")
            lines.append(f'  {sid} [shape=doublecircle label="{sid}\\n({action_label})"];')

        target_syms: dict[int, list[int]] = defaultdict(list)
        for sym, target in state.transitions.items():
            target_syms[target].append(sym)

        for target, syms in target_syms.items():
            label = _format_symbol_set(syms)
            label = label.replace('"', '\\"')
            lines.append(f'  {sid} -> {target} [label="{label}"];')

    lines.append("}")

    dot_content = "\n".join(lines)
    dot_path = f"{filename}.dot"
    with open(dot_path, "w", encoding="utf-8") as f:
        f.write(dot_content)
    _try_render_dot(dot_path)
    if not silent:
        print(f"[INFO] DFA diagram written to {dot_path}")
    return dot_path


def _format_symbol_set(syms: list[int]) -> str:
    if len(syms) > 10:
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
    if ch == ord("\n"):
        return "\\n"
    if ch == ord("\t"):
        return "\\t"
    if ch == ord(" "):
        return "SP"
    if 33 <= ch < 127:
        c = chr(ch)
        if c in '"\\':
            return f"\\{c}"
        return c
    return f"x{ch:02x}"


def _find_ranges(sorted_ints: list[int]) -> list[tuple[int, int]]:
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
