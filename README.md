# YALex — Yet Another Lex Generator

A lexer generator that reads `.yal` specification files (based on ocamllex/Lex syntax) and produces standalone Python lexical analyzers.

## Project Structure

```
yalex.py              # Main generator (all-in-one)
ejemplo.yal           # Simple arithmetic lexer spec
slr_lexer.yal         # Advanced language lexer spec
test_input.txt        # Sample input for testing
README.md             # This file
```

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
python yalex.py ejemplo.yal -o my_lexer
```

This produces:
- `my_lexer.py` — the generated lexer
- `my_lexer_trees/` — DOT files for each regex expression tree
- `my_lexer_dfa.dot` — the DFA state diagram

### Step 2: Run the generated lexer on input

```bash
python my_lexer.py test_input.txt
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

## Implementation Details

### Algorithms Used

- **Thompson's Construction** — Regex AST → NFA with epsilon transitions
- **Subset Construction** — NFA → DFA via powerset/epsilon-closure algorithm
- **Hopcroft's Minimization** — DFA state minimization via partition refinement
- **Longest Match** — The generated lexer always finds the longest matching prefix
- **Priority by Order** — On ties, the first rule defined wins

### Lexer Matching Strategy

The generated lexer implements the standard maximal-munch algorithm:

1. Start at the DFA's initial state
2. Read characters, advancing through the DFA
3. Track the last accepting state seen (and which rule it belongs to)
4. When the DFA gets stuck (no valid transition), backtrack to the last accepting state
5. Execute the corresponding action
6. Repeat from the new position

## Requirements

- Python 3.7+
- Graphviz (optional, for rendering DOT files to PNG)

## Course Information

CC3071 — Diseño de Lenguajes de Programación  
Universidad del Valle de Guatemala  
Facultad de Ingeniería — Departamento de Ciencia de la Computación