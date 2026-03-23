"""Parse .yal specification files into YALexSpec."""

from __future__ import annotations

from dataclasses import dataclass

from yalex.diagnostics import SourceSpan, SpecParseError


@dataclass
class YALexRule:
    pattern_str: str
    action: str  # code inside { }


@dataclass
class YALexSpec:
    header: str
    trailer: str
    definitions: list[tuple[str, str]]  # (name, regex_str)
    entrypoint: str
    rules: list[YALexRule]


def parse_yalex_file(filepath: str) -> YALexSpec:
    """Parse a .yal file into a YALexSpec."""
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    return parse_yalex_string(content, source_name=filepath)


def parse_yalex_string(content: str, source_name: str = "<string>") -> YALexSpec:
    """Parse .yal content from a string (useful for tests)."""
    content = _remove_comments(content)

    header = ""
    trailer = ""
    definitions: list[tuple[str, str]] = []
    entrypoint = "tokens"
    rules: list[YALexRule] = []

    pos = 0
    length = len(content)

    def skip_ws() -> None:
        nonlocal pos
        while pos < length and content[pos] in " \t\r\n":
            pos += 1

    # --- Try to parse header { ... } ---
    skip_ws()
    if pos < length and content[pos] == "{":
        header, pos = _extract_braces(content, pos)

    # --- Parse let definitions ---
    skip_ws()
    while pos < length:
        skip_ws()
        if content[pos : pos + 3] == "let":
            pos += 3
            skip_ws()
            ident_start = pos
            while pos < length and (content[pos].isalnum() or content[pos] == "_"):
                pos += 1
            ident = content[ident_start:pos]
            skip_ws()
            if pos >= length or content[pos] != "=":
                got = content[pos] if pos < length else "EOF"
                raise SpecParseError(
                    f"{source_name}: expected '=' after let {ident}, got {got!r} at offset {pos}",
                    SourceSpan(pos, pos + 1),
                )
            pos += 1
            skip_ws()
            regex_str, pos = _read_let_regex(content, pos)
            definitions.append((ident, regex_str.strip()))
        elif content[pos : pos + 4] == "rule":
            break
        else:
            pos += 1

    # --- Parse rule section ---
    skip_ws()
    if content[pos : pos + 4] == "rule":
        pos += 4
        skip_ws()
        ep_start = pos
        while pos < length and (content[pos].isalnum() or content[pos] == "_"):
            pos += 1
        entrypoint = content[ep_start:pos]
        skip_ws()
        while pos < length and content[pos] != "=":
            pos += 1
        if pos >= length:
            raise SpecParseError(
                f"{source_name}: expected '=' in rule header",
                SourceSpan(max(0, pos - 1), pos),
            )
        pos += 1
        skip_ws()

        rules = _parse_rules(content, pos)
        last_rule_end = _find_rules_end(content, pos)
        pos = last_rule_end

    # --- Try to parse trailer { ... } ---
    skip_ws()
    if pos < length and content[pos] == "{":
        trailer, pos = _extract_braces(content, pos)

    return YALexSpec(header, trailer, definitions, entrypoint, rules)


def _remove_comments(text: str) -> str:
    """Remove (* ... *) comments, handling nesting."""
    result = []
    i = 0
    while i < len(text):
        if i + 1 < len(text) and text[i] == "(" and text[i + 1] == "*":
            depth = 1
            i += 2
            while i < len(text) and depth > 0:
                if i + 1 < len(text) and text[i] == "(" and text[i + 1] == "*":
                    depth += 1
                    i += 2
                elif i + 1 < len(text) and text[i] == "*" and text[i + 1] == ")":
                    depth -= 1
                    i += 2
                else:
                    i += 1
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


def _extract_braces(text: str, pos: int) -> tuple[str, int]:
    """Extract content between { and }, handling nesting. Returns (content, new_pos)."""
    if pos >= len(text) or text[pos] != "{":
        raise SpecParseError(
            f"expected '{{' at offset {pos}",
            SourceSpan(pos, min(pos + 1, len(text))),
        )
    depth = 1
    start = pos + 1
    pos += 1
    while pos < len(text) and depth > 0:
        if text[pos] == "{":
            depth += 1
        elif text[pos] == "}":
            depth -= 1
        pos += 1
    return text[start : pos - 1].strip(), pos


def _read_let_regex(text: str, pos: int) -> tuple[str, int]:
    """Read a regex from a let definition until unambiguous end."""
    start = pos
    length = len(text)
    while pos < length:
        rest = text[pos:].lstrip()
        if rest.startswith("let ") or rest.startswith("rule "):
            break
        while pos < length and text[pos] != "\n":
            if text[pos] == "'":
                pos += 1
                while pos < length and text[pos] != "'":
                    if text[pos] == "\\":
                        pos += 1
                    pos += 1
                pos += 1
            elif text[pos] == '"':
                pos += 1
                while pos < length and text[pos] != '"':
                    if text[pos] == "\\":
                        pos += 1
                    pos += 1
                pos += 1
            elif text[pos] == "[":
                while pos < length and text[pos] != "]":
                    pos += 1
                pos += 1
            else:
                pos += 1
        if pos < length:
            pos += 1
    return text[start:pos], pos


def _parse_rules(text: str, pos: int) -> list[YALexRule]:
    """Parse rule alternatives: pattern { action } | pattern { action } ..."""
    rules: list[YALexRule] = []
    length = len(text)

    def skip_ws() -> None:
        nonlocal pos
        while pos < length and text[pos] in " \t\r\n":
            pos += 1

    while pos < length:
        skip_ws()
        if pos >= length:
            break

        if text[pos] == "|":
            pos += 1
            skip_ws()

        if pos >= length:
            break

        if text[pos] == "{" and rules:
            break

        pattern, pos = _read_rule_pattern(text, pos)
        if not pattern.strip():
            break

        skip_ws()

        action = ""
        if pos < length and text[pos] == "{":
            action, pos = _extract_braces(text, pos)

        rules.append(YALexRule(pattern.strip(), action.strip()))

    return rules


def _read_rule_pattern(text: str, pos: int) -> tuple[str, int]:
    """Read a rule pattern until we hit '{' (action) or '|' at top level."""
    start = pos
    length = len(text)
    depth_bracket = 0
    depth_paren = 0

    while pos < length:
        ch = text[pos]
        if ch == "'":
            pos += 1
            while pos < length and text[pos] != "'":
                if text[pos] == "\\":
                    pos += 1
                pos += 1
            pos += 1
        elif ch == '"':
            pos += 1
            while pos < length and text[pos] != '"':
                if text[pos] == "\\":
                    pos += 1
                pos += 1
            pos += 1
        elif ch == "[":
            depth_bracket += 1
            pos += 1
        elif ch == "]":
            depth_bracket -= 1
            pos += 1
        elif ch == "(":
            depth_paren += 1
            pos += 1
        elif ch == ")":
            depth_paren -= 1
            pos += 1
        elif ch == "{" and depth_bracket == 0 and depth_paren == 0:
            break
        elif ch == "|" and depth_bracket == 0 and depth_paren == 0:
            break
        else:
            pos += 1

    return text[start:pos], pos


def _find_rules_end(text: str, pos: int) -> int:
    """Find the position after all rules have been parsed."""
    length = len(text)
    last_action_end = pos
    while pos < length:
        if text[pos] == "{":
            depth = 1
            pos += 1
            while pos < length and depth > 0:
                if text[pos] == "{":
                    depth += 1
                elif text[pos] == "}":
                    depth -= 1
                pos += 1
            last_action_end = pos
        elif text[pos] in " \t\r\n":
            pos += 1
        elif text[pos] == "|":
            pos += 1
        else:
            line_start = pos
            while pos < length and text[pos] not in "{|\n":
                pos += 1
            if pos < length and text[pos] == "{":
                segment = text[line_start:pos].strip()
                if not segment:
                    return line_start
                continue
            elif pos < length and text[pos] == "|":
                continue
            elif pos < length and text[pos] == "\n":
                pos += 1
                continue
            else:
                break
    return last_action_end
