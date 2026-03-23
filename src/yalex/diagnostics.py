"""Errors and source locations for YALex."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSpan:
    """A range in source text (0-based offset, inclusive start, exclusive end)."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start > self.end:
            raise ValueError("SourceSpan: start must be <= end")


class YalexError(Exception):
    """Base class for YALex errors."""

    pass


class SpecParseError(YalexError):
    """Error while parsing a .yal specification file."""

    def __init__(self, message: str, span: SourceSpan | None = None) -> None:
        super().__init__(message)
        self.span = span


class RegexParseError(YalexError):
    """Error while parsing a regex sub-expression."""

    def __init__(self, message: str, offset: int | None = None) -> None:
        super().__init__(message)
        self.offset = offset
