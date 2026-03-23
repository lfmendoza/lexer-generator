"""Combine NFAs and build minimized DFA; high-level compile API."""

from __future__ import annotations

import os
from dataclasses import dataclass

from yalex.codegen import generate_lexer
from yalex.dfa import DFAState, minimize_dfa, nfa_to_dfa
from yalex.dot import dfa_to_dot, generate_all_trees
from yalex.nfa import NFA, NFABuilder
from yalex.regex_parser import RegexParser
from yalex.spec_parser import YALexSpec, parse_yalex_file
from yalex.trace import TraceEventKind, TraceRecorder, null_trace


def build_combined_dfa(
    spec: YALexSpec,
) -> tuple[dict[int, DFAState], int, list[str]]:
    """
    Build a single DFA that recognizes all rule patterns.
    Returns (dfa_states, start_id, actions_list).
    """
    definitions = dict(spec.definitions)
    builder = NFABuilder()

    super_start = builder.new_state()
    all_states = {super_start.id: super_start}
    actions: list[str] = []

    for i, rule in enumerate(spec.rules):
        parser = RegexParser(rule.pattern_str, definitions)
        ast = parser.parse()
        nfa = builder.build(ast, rule_index=i)
        super_start.transitions[None].append(nfa.start)
        all_states.update(nfa.states)
        actions.append(rule.action)

    combined_accept = builder.new_state()
    all_states[combined_accept.id] = combined_accept

    combined_nfa = NFA(super_start.id, combined_accept.id, all_states)

    dfa_states, dfa_start = nfa_to_dfa(combined_nfa)
    dfa_states, dfa_start = minimize_dfa(dfa_states, dfa_start)

    return dfa_states, dfa_start, actions


@dataclass
class CompileOptions:
    """Options for compile_from_file / compile_spec."""

    output_name: str | None = None
    emit_trees: bool = True
    emit_dfa_graph: bool = True
    trace: TraceRecorder | None = None
    emit_info_messages: bool = True


@dataclass
class CompileResult:
    """Result of a full compile pipeline."""

    output_path: str
    dfa_state_count: int


def compile_from_file(
    input_path: str,
    options: CompileOptions | None = None,
    *,
    spec: YALexSpec | None = None,
) -> CompileResult:
    """
    Full pipeline: parse .yal (unless spec is provided), optional DOT artifacts,
    build DFA, emit lexer .py. Returns path to generated lexer file.
    """
    opts = options or CompileOptions()
    trace = opts.trace if opts.trace is not None else null_trace()

    if spec is None:
        spec = parse_yalex_file(input_path)
    trace.emit(
        TraceEventKind.SPEC_PARSED,
        definitions=len(spec.definitions),
        rules=len(spec.rules),
        entrypoint=spec.entrypoint,
    )

    base = opts.output_name or os.path.splitext(os.path.basename(input_path))[0] + "_lexer"
    output_path = base + ".py"
    tree_dir = base + "_trees"

    if opts.emit_trees:
        generate_all_trees(spec, tree_dir, silent=not opts.emit_info_messages)
        trace.emit(TraceEventKind.TREES_EMITTED, directory=tree_dir)

    dfa_states, dfa_start, actions = build_combined_dfa(spec)
    trace.emit(TraceEventKind.DFA_MINIMIZED, states=len(dfa_states))

    if opts.emit_dfa_graph:
        dot_path = dfa_to_dot(
            dfa_states,
            dfa_start,
            actions,
            base + "_dfa",
            silent=not opts.emit_info_messages,
        )
        trace.emit(TraceEventKind.DFA_DOT_WRITTEN, path=dot_path)

    generate_lexer(
        spec,
        dfa_states,
        dfa_start,
        actions,
        output_path,
        silent=not opts.emit_info_messages,
    )
    trace.emit(TraceEventKind.CODE_WRITTEN, path=output_path)

    return CompileResult(output_path=output_path, dfa_state_count=len(dfa_states))


def compile_spec(spec: YALexSpec, output_path: str) -> None:
    """
    Build DFA from an in-memory spec and write lexer to output_path.
    Does not emit DOT trees (use lower-level functions for tests).
    """
    dfa_states, dfa_start, actions = build_combined_dfa(spec)
    generate_lexer(spec, dfa_states, dfa_start, actions, output_path)
