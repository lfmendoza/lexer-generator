# YALex — Yet Another Lex Generator

A lexer generator that reads `.yal` specification files (based on ocamllex/Lex syntax) and produces standalone Python lexical analyzers.

## Project layout

```
src/yalex/
specs/yal/                    # especificaciones léxicas (.yal)
  arithmetic_expression.yal   # expresiones y asignación (curso / pruebas)
  imperative_core.yal         # lenguaje imperativo amplio (reservadas, literales, operadores)
samples/inputs/               # entradas de ejemplo para los lexers generados
  arithmetic_expressions.txt
  imperative_core_sample.txt
yalex_cli.py
pyproject.toml
tests/
```

```bash
pip install -e ".[dev]"
```

Run `yalex`, `python -m yalex`, or `python yalex_cli.py`.

## How It Works

The pipeline follows standard compiler construction theory:

1. **Parse the `.yal` file** — extracts header, `let` definitions, `rule` patterns + actions, and trailer
2. **Parse each regex** — converts YALex regex syntax into an Abstract Syntax Tree (AST)
3. **Build NFAs** — uses Thompson's Construction for each rule pattern
4. **Combine into one NFA** — connects all rule NFAs via epsilon transitions from a super-start state
5. **Convert to DFA** — subset construction algorithm
6. **Minimize DFA** — Hopcroft-style partition refinement
7. **Generate lexer** — emits a standalone Python file with the DFA transition table embedded
8. **Visualize** — outputs Graphviz DOT files for expression trees and the DFA

## Usage

### Step 1: Generate a lexer from a `.yal` file

```bash
yalex specs/yal/arithmetic_expression.yal -o my_lexer
# or: python yalex_cli.py specs/yal/arithmetic_expression.yal -o my_lexer
```

Genera `my_lexer.py`, `my_lexer_trees/` (DOT de árboles de regex) y `my_lexer_dfa.dot`.

Segundo ejemplo (lenguaje imperativo):

```bash
yalex specs/yal/imperative_core.yal -o imp_lexer
python imp_lexer.py samples/inputs/imperative_core_sample.txt
```

### Step 2: Run the generated lexer on input

```bash
python my_lexer.py samples/inputs/arithmetic_expressions.txt
```

Output:
```
=== TOKENS ===
('ID', 'x', 1, 1)
('ASSIGN', '=', 1, 3)
('NUMBER', 3, 1, 5)
('PLUS', '+', 1, 7)
('NUMBER', 42, 1, 9)
...
```

### Optional: Render DOT files to images

If you have Graphviz installed:

```bash
dot -Tpng my_lexer_dfa.dot -o my_lexer_dfa.png
dot -Tpng my_lexer_trees/combined.dot -o combined_tree.png
```

## Command-Line Options

| Flag | Description |
|------|-------------|
| `-o NAME` | Output filename (without `.py` extension) |
| `--no-trees` | Skip expression tree DOT generation |
| `--no-dfa-graph` | Skip DFA diagram generation |
| `-v` / `--verbose` | Verbose logging |
| `-q` / `--quiet` | Minimal output (suppresses `[INFO]` lines from codegen/DOT) |
| `--trace human` / `json` / `off` | Pipeline trace events (default: off) |

## YALex Syntax Reference

### File Structure

```
(* comments *)
{ optional header code }
let name = regex
...
rule entrypoint =
    pattern   { action }
  | pattern   { action }
  ...
{ optional trailer code }
```

### Regex Syntax

| Syntax | Meaning |
|--------|---------|
| `'c'` | Character literal |
| `'\n'` | Escape sequence |
| `_` | Any character |
| `"abc"` | String (concatenation of chars) |
| `['a'-'z']` | Character class with range |
| `['a' 'b' 'c']` | Character class (set) |
| `[^'0'-'9']` | Negated character class |
| `r1 \| r2` | Union (alternation) |
| `r1 r2` | Concatenation |
| `r*` | Kleene star |
| `r+` | Positive closure |
| `r?` | Optional |
| `r1 # r2` | Set difference |
| `(r)` | Grouping |
| `eof` | End of file |
| `ident` | Reference to a `let` definition |

### Operator Precedence (highest to lowest)

1. `#` (set difference)
2. `*`, `+`, `?`
3. Concatenation
4. `|` (union)

### Actions

Actions are Python code blocks enclosed in `{ }`. Available variables inside actions:

- `lxm` — the matched lexeme (string)
- `lexeme` — same as `lxm`
- `line` — line number where the match starts
- `col` — column number where the match starts
- `lexbuf` — reference to the Lexer object

Return `None` to skip the token (e.g., for whitespace). Return any value to emit it as a token.

## Behaviour

Pipeline: regex AST → Thompson NFA → combined NFA → subset DFA → Hopcroft minimization → emitted lexer. Matching is longest-prefix; on equal length, the earlier rule in the spec wins.

Evite el nombre de regla `tokens` como punto de entrada (`rule tokens =`): en el código generado entra en conflicto con el atributo `Lexer.tokens` (lista). Use por ejemplo `gettoken`, `tokenize`, etc.

Solo dependencias estándar de Python en el proyecto y en el código generado por YALex.

## Requirements

- Python 3.10+
- Graphviz (optional, for rendering DOT to PNG)

## Development

```bash
make install
make check
pre-commit install
```

Without `make` (e.g. Windows): `pip install -e ".[dev]"`, then `ruff check src tests yalex_cli.py`, `mypy src/yalex`, `pytest`.

## Course Information

CC3071 — Diseño de Lenguajes de Programación  
Universidad del Valle de Guatemala  
Facultad de Ingeniería — Departamento de Ciencia de la Computación