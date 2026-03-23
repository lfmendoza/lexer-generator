"""YALex — lexer generator for `.yal` specifications."""

from __future__ import annotations

__version__ = "0.1.0"

from yalex.diagnostics import RegexParseError, SourceSpan, SpecParseError, YalexError
from yalex.pipeline import (
    CompileOptions,
    CompileResult,
    build_combined_dfa,
    compile_from_file,
    compile_spec,
)
from yalex.spec_parser import YALexRule, YALexSpec, parse_yalex_file, parse_yalex_string
from yalex.trace import TraceEventKind, TraceRecorder, null_trace

__all__ = [
    "__version__",
    "YalexError",
    "SpecParseError",
    "RegexParseError",
    "SourceSpan",
    "YALexSpec",
    "YALexRule",
    "parse_yalex_file",
    "parse_yalex_string",
    "build_combined_dfa",
    "compile_from_file",
    "compile_spec",
    "CompileOptions",
    "CompileResult",
    "TraceRecorder",
    "TraceEventKind",
    "null_trace",
]
