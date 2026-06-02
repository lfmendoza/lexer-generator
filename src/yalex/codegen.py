"""Emit standalone Python lexer from a minimized DFA."""

from __future__ import annotations

import re

from yalex.dfa import DFAState
from yalex.spec_parser import YALexSpec

_LEXBUF_SKIP = re.compile(r"\breturn\s+lexbuf\b")


def _normalize_lexer_action(action: str) -> str:
    return _LEXBUF_SKIP.sub("return None", action.strip())


def generate_lexer(
    spec: YALexSpec,
    dfa_states: dict[int, DFAState],
    dfa_start: int,
    actions: list[str],
    output_path: str,
    *,
    silent: bool = False,
) -> None:
    """Generate a standalone Python lexer file."""

    trans_table: dict[int, dict[int, int]] = {}
    for sid, state in dfa_states.items():
        trans_table[sid] = dict(state.transitions)

    accept_table: dict[int, int] = {}
    for sid, state in dfa_states.items():
        if state.is_accept:
            accept_table[sid] = state.rule_index

    action_cases = []
    for i, action in enumerate(actions):
        if action:
            body = _normalize_lexer_action(action)
            action_cases.append(f"        if rule_index == {i}:\n            {body}")
        else:
            action_cases.append(f"        if rule_index == {i}:\n            pass")

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
    def __init__(self, line, col, char):
        self.line = line
        self.col = col
        self.char = char
        msg = (
            "LEXICAL ERROR at line {{}}, column {{}}: "
            "Unrecognized character {{!r}}".format(line, col, char)
        )
        super().__init__(msg)


class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens = []

    def {spec.entrypoint}(self):
        while self.pos < len(self.text):
            token = self._next_token()
            if token is not None:
                self.tokens.append(token)
        if self.pos == len(self.text):
            token = self._next_token()
            if token is not None:
                self.tokens.append(token)
        return self.tokens

    def _next_token(self):
        state = _START_STATE
        last_accept_pos = -1
        last_accept_rule = -1
        current_pos = self.pos

        while current_pos <= len(self.text):
            if state in _ACCEPT_TABLE:
                last_accept_pos = current_pos
                last_accept_rule = _ACCEPT_TABLE[state]

            if current_pos >= len(self.text):
                trans = _TRANS_TABLE.get(state, {{}})
                if -1 in trans:
                    state = trans[-1]
                    current_pos += 1
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
            lxm = lexeme
            lexbuf = None

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

            result = self._execute_action(rule_index, lexeme, lxm, start_line, start_col)
            return result
        elif last_accept_rule >= 0 and last_accept_pos == self.pos:
            self.pos += 1
            return None
        else:
            if self.pos >= len(self.text):
                return None
            bad_char = self.text[self.pos]
            raise LexerError(self.line, self.col, bad_char)

    def _execute_action(self, rule_index, lexeme, lxm, line, col):
        lexbuf = self
{action_dispatch}
        return None


def _lexical_alignment_view(text, tokens_list):
    lines = text.splitlines()
    usable = [
        t
        for t in tokens_list
        if t is not None and isinstance(t, tuple) and len(t) >= 4
    ]
    if not usable:
        print(
            "(Vista léxica: no hay tokens con forma (tipo, valor, línea, columna).)",
            file=sys.stderr,
        )
        return
    by_line = {{}}
    for t in usable:
        by_line.setdefault(t[2], []).append(t)
    print("=== Vista léxica (texto y tipos alineados) ===")
    for ln in sorted(by_line.keys()):
        ts = sorted(by_line[ln], key=lambda t: t[3])
        src = lines[ln - 1] if 1 <= ln <= len(lines) else ""
        seq = " ".join(str(t[0]) for t in ts)
        detail_parts = []
        for t in ts:
            detail_parts.append(str(t[0]) + "(" + repr(t[1]) + ")")
        detail = " ".join(detail_parts)
        print("--- Línea %s ---" % (ln,))
        print("Texto:   " + repr(src))
        print("Tipos:   " + seq)
        print("Detalle: " + detail)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Lexer generado por YALex")
    parser.add_argument("input", help="Archivo de entrada")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help=(
            "Tras la tabla, muestra por línea el texto y la secuencia de tipos (p. ej. ID + ID)"
        ),
    )
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        text = f.read()

    lexer = Lexer(text)
    try:
        tokens = lexer.{spec.entrypoint}()
    except EOFError:
        tokens = lexer.tokens
    except LexerError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)

    print("=== TOKENS ===")
    for tok in tokens:
        if tok is not None:
            print(tok)
    print(f"=== {{len([t for t in tokens if t is not None])}} tokens found ===")
    if args.pretty:
        print()
        _lexical_alignment_view(text, tokens)


if __name__ == "__main__":
    main()

# --- Trailer ---
{spec.trailer}
'''

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)

    if not silent:
        print(f"[INFO] Lexer generated: {output_path}")
