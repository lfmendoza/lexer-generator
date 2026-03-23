"""Command-line interface for YALex."""

from __future__ import annotations

import argparse
import logging
import os

from yalex.pipeline import CompileOptions, compile_from_file
from yalex.spec_parser import parse_yalex_file
from yalex.trace import TraceRecorder

_LOG = logging.getLogger("yalex")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="YALex - Yet Another Lex Generator")
    parser.add_argument("input", help="Input .yal file")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output lexer filename (without extension)",
    )
    parser.add_argument("--no-trees", action="store_true", help="Skip expression tree generation")
    parser.add_argument("--no-dfa-graph", action="store_true", help="Skip DFA diagram generation")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    parser.add_argument("-q", "--quiet", action="store_true", help="Minimal output")
    parser.add_argument(
        "--trace",
        choices=("human", "json", "off"),
        default="off",
        help="Pipeline trace: human-readable lines, JSON lines, or off (default)",
    )
    args = parser.parse_args(argv)

    if args.verbose and args.quiet:
        parser.error("Cannot use both --verbose and --quiet")

    log_level = logging.WARNING if args.quiet else (logging.DEBUG if args.verbose else logging.INFO)
    logging.basicConfig(level=log_level, format="%(message)s")

    trace_mode = args.trace
    trace = TraceRecorder(mode=trace_mode)

    output_name = args.output or os.path.splitext(os.path.basename(args.input))[0] + "_lexer"
    output_path = output_name + ".py"

    if not args.quiet:
        print(f"[YALex] Parsing {args.input}...")
    spec = parse_yalex_file(args.input)
    if not args.quiet:
        print(f"[YALex] Found {len(spec.definitions)} definitions, {len(spec.rules)} rules")
        print(f"[YALex] Entrypoint: {spec.entrypoint}")
        for name, regex_str in spec.definitions:
            print(f"  let {name} = {regex_str}")
        for i, rule in enumerate(spec.rules):
            action_preview = rule.action[:40] if rule.action else "(no action)"
            print(f"  rule {i}: {rule.pattern_str}  ->  {action_preview}")

    if not args.quiet and not args.no_trees:
        print("\n[YALex] Generating expression trees...")
    if not args.quiet:
        print("\n[YALex] Building NFA...")
        print("[YALex] Converting NFA -> DFA (subset construction)...")
        print("[YALex] Minimizing DFA...")

    opts = CompileOptions(
        output_name=output_name,
        emit_trees=not args.no_trees,
        emit_dfa_graph=not args.no_dfa_graph,
        trace=trace,
        emit_info_messages=not args.quiet,
    )

    try:
        result = compile_from_file(args.input, opts, spec=spec)
    except Exception as e:
        _LOG.error("%s", e)
        raise SystemExit(1) from e

    if not args.quiet:
        print(f"[YALex] DFA has {result.dfa_state_count} states")
        print(f"\n[YALex] Generating lexer -> {result.output_path}")
        print(f"\n[YALex] Done! Run your lexer with:\n  python {output_path} <input_file>")


if __name__ == "__main__":
    main()
