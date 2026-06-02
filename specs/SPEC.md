# PICO — A Minimal Programming Language for YALex

Implementación: [`specs/yal/pico.yal`](yal/pico.yal). Ejemplos: [`samples/inputs/pico/`](../samples/inputs/pico/).

## Overview

**PICO** (*Pico Interpreted Command Operations*) is a deliberately minimal, expression-oriented language designed for University compiler courses. It is esoteric enough to be interesting but simple enough to be fully specified in a single YALex file.

### Design Philosophy

- Everything is either a **number**, a **string**, or a **boolean**
- There are no function declarations — only **macros** (named expressions)
- Control flow uses `when`/`otherwise` (no `else if`)
- Loops use `repeat ... until`
- Output via `emit`
- Comments use `--`

---

## PICO Token Reference

| Token Name       | Description                                  | Example                    |
|------------------|----------------------------------------------|----------------------------|
| `INT_LIT`        | Integer literal                              | `42`, `0`, `7`             |
| `FLOAT_LIT`      | Floating-point literal                       | `3.14`, `0.5`              |
| `STRING_LIT`     | Double-quoted string                         | `"hello"`                  |
| `BOOL_LIT`       | Boolean literal                              | `true`, `false`            |
| `IDENT`          | Identifier (macro/variable name)             | `x`, `myVal`, `counter`    |
| `ASSIGN`         | Assignment operator                          | `<-`                       |
| `PLUS`           | Addition                                     | `+`                        |
| `MINUS`          | Subtraction                                  | `-`                        |
| `TIMES`          | Multiplication                               | `*`                        |
| `DIV`            | Division                                     | `/`                        |
| `MOD`            | Modulo                                       | `%`                        |
| `EQ`             | Equality comparison                          | `==`                       |
| `NEQ`            | Not equal                                    | `!=`                       |
| `LT`             | Less than                                    | `<`                        |
| `GT`             | Greater than                                 | `>`                        |
| `LEQ`            | Less than or equal                           | `<=`                       |
| `GEQ`            | Greater than or equal                        | `>=`                       |
| `AND`            | Logical and                                  | `&&`                       |
| `OR`             | Logical or                                   | `\|\|`                     |
| `NOT`            | Logical not                                  | `!`                        |
| `LPAREN`         | Left parenthesis                             | `(`                        |
| `RPAREN`         | Right parenthesis                            | `)`                        |
| `LBRACE`         | Left brace (block open)                      | `{`                        |
| `RBRACE`         | Right brace (block close)                    | `}`                        |
| `SEMICOLON`      | Statement terminator                         | `;`                        |
| `COMMA`          | Separator (macro args)                       | `,`                        |
| `KW_MACRO`       | Keyword: macro definition                    | `macro`                    |
| `KW_EMIT`        | Keyword: output statement                    | `emit`                     |
| `KW_WHEN`        | Keyword: conditional                         | `when`                     |
| `KW_OTHERWISE`   | Keyword: else branch                         | `otherwise`                |
| `KW_REPEAT`      | Keyword: loop start                          | `repeat`                   |
| `KW_UNTIL`       | Keyword: loop condition                      | `until`                    |
| `KW_LET`         | Keyword: variable binding                    | `let`                      |

> Whitespace (spaces, tabs, newlines) and comments (`-- ...`) are **skipped** and produce no tokens.

---

## YALex Specification File

```
(* pico.yal — YALex specification for the PICO language *)

{
(* Generated lexer for PICO language *)
(* Tokens: INT_LIT FLOAT_LIT STRING_LIT BOOL_LIT IDENT *)
(*         ASSIGN PLUS MINUS TIMES DIV MOD              *)
(*         EQ NEQ LT GT LEQ GEQ AND OR NOT              *)
(*         LPAREN RPAREN LBRACE RBRACE                   *)
(*         SEMICOLON COMMA                               *)
(*         KW_MACRO KW_EMIT KW_WHEN KW_OTHERWISE        *)
(*         KW_REPEAT KW_UNTIL KW_LET                    *)
}

(* ── Character classes ──────────────────────────────── *)

let digit      = ['0'-'9']
let nonzero    = ['1'-'9']
let letter     = ['a'-'z' 'A'-'Z']
let alphanum   = letter | digit | '_'

(* ── Numeric literals ───────────────────────────────── *)

let int_lit    = '0' | nonzero digit*
let float_lit  = int_lit '.' digit+

(* ── String literal (no embedded newlines) ──────────── *)

let str_char   = [^ '"' '\n' '\\'] | '\\' _
let string_lit = '"' str_char* '"'

(* ── Identifiers ────────────────────────────────────── *)

let ident      = letter alphanum*

(* ── Line comment ───────────────────────────────────── *)

let line_cmt   = '-' '-' [^ '\n']* '\n'

(* ══════════════════════════════════════════════════════ *)

rule gettoken =

    (* Skip whitespace *)
    [' ' '\t' '\n' '\r']          { return lexbuf }

    (* Skip line comments *)
  | line_cmt                      { return lexbuf }

    (* Floating-point — must come BEFORE int_lit *)
  | float_lit                     { return FLOAT_LIT(lxm) }

    (* Integer *)
  | int_lit                       { return INT_LIT(lxm) }

    (* String literal *)
  | string_lit                    { return STRING_LIT(lxm) }

    (* Boolean literals — must come BEFORE ident *)
  | "true"                        { return BOOL_LIT(lxm) }
  | "false"                       { return BOOL_LIT(lxm) }

    (* Keywords — must come BEFORE ident *)
  | "macro"                       { return KW_MACRO }
  | "emit"                        { return KW_EMIT }
  | "when"                        { return KW_WHEN }
  | "otherwise"                   { return KW_OTHERWISE }
  | "repeat"                      { return KW_REPEAT }
  | "until"                       { return KW_UNTIL }
  | "let"                         { return KW_LET }

    (* Identifier *)
  | ident                         { return IDENT(lxm) }

    (* Two-character operators — must come BEFORE single-char *)
  | "<-"                          { return ASSIGN }
  | "=="                          { return EQ }
  | "!="                          { return NEQ }
  | "<="                          { return LEQ }
  | ">="                          { return GEQ }
  | "&&"                          { return AND }
  | "||"                          { return OR }

    (* Single-character operators *)
  | '+'                           { return PLUS }
  | '-'                           { return MINUS }
  | '*'                           { return TIMES }
  | '/'                           { return DIV }
  | '%'                           { return MOD }
  | '<'                           { return LT }
  | '>'                           { return GT }
  | '!'                           { return NOT }

    (* Delimiters *)
  | '('                           { return LPAREN }
  | ')'                           { return RPAREN }
  | '{'                           { return LBRACE }
  | '}'                           { return RBRACE }
  | ';'                           { return SEMICOLON }
  | ','                           { return COMMA }

    (* End of file *)
  | eof                           { raise( 'End of input' ) }
```

---

## Source Files That SHOULD Be Lexed Successfully

### ✅ Test File 1 — `hello.pico`

```pico
-- A simple greeting program
let name <- "world";
emit "Hello, ";
emit name;
```

**Expected token output:**

```
KW_LET
IDENT("name")
ASSIGN
STRING_LIT("\"world\"")
SEMICOLON
KW_EMIT
STRING_LIT("\"Hello, \"")
SEMICOLON
KW_EMIT
IDENT("name")
SEMICOLON
```
In your case it's not strictly necessary to provide some tokens with its lxm, e.g., IDENT("name"), it should be enough with the token, i.e., IDENT.
---

### ✅ Test File 2 — `arithmetic.pico`

```pico
-- Basic arithmetic
let x <- 10;
let y <- 3;
let result <- (x + y) * 2;
emit result;
```

**Expected token output:**

```
KW_LET
IDENT("x")
ASSIGN
INT_LIT("10")
SEMICOLON
KW_LET
IDENT("y")
ASSIGN
INT_LIT("3")
SEMICOLON
KW_LET
IDENT("result")
ASSIGN
LPAREN
IDENT("x")
PLUS
IDENT("y")
RPAREN
TIMES
INT_LIT("2")
SEMICOLON
KW_EMIT
IDENT("result")
SEMICOLON
```

---

### ✅ Test File 3 — `conditional.pico`

```pico
-- Conditional with boolean
let score <- 85;
let passed <- score >= 60;
when (passed) {
    emit "Approved";
} otherwise {
    emit "Failed";
}
```

**Expected token output:**

```
KW_LET
IDENT("score")
ASSIGN
INT_LIT("85")
SEMICOLON
KW_LET
IDENT("passed")
ASSIGN
IDENT("score")
GEQ
INT_LIT("60")
SEMICOLON
KW_WHEN
LPAREN
IDENT("passed")
RPAREN
LBRACE
KW_EMIT
STRING_LIT("\"Approved\"")
SEMICOLON
RBRACE
KW_OTHERWISE
LBRACE
KW_EMIT
STRING_LIT("\"Failed\"")
SEMICOLON
RBRACE
```

---

### ✅ Test File 4 — `loop.pico`

```pico
-- Count down from 5
let count <- 5;
repeat {
    emit count;
    let count <- count - 1;
} until (count == 0);
```

**Expected token output:**

```
KW_LET
IDENT("count")
ASSIGN
INT_LIT("5")
SEMICOLON
KW_REPEAT
LBRACE
KW_EMIT
IDENT("count")
SEMICOLON
KW_LET
IDENT("count")
ASSIGN
IDENT("count")
MINUS
INT_LIT("1")
SEMICOLON
RBRACE
KW_UNTIL
LPAREN
IDENT("count")
EQ
INT_LIT("0")
RPAREN
SEMICOLON
```

---

### ✅ Test File 5 — `macro.pico`

```pico
-- Macro (named expression)
macro double(n) {
    n * 2
}

let val <- 7;
emit double(val);
```

**Expected token output:**

```
KW_MACRO
IDENT("double")
LPAREN
IDENT("n")
RPAREN
LBRACE
IDENT("n")
TIMES
INT_LIT("2")
RBRACE
KW_LET
IDENT("val")
ASSIGN
INT_LIT("7")
SEMICOLON
KW_EMIT
IDENT("double")
LPAREN
IDENT("val")
RPAREN
SEMICOLON
```

---

### ✅ Test File 6 — `floats_and_logic.pico`

```pico
-- Floating point and logical operators
let pi <- 3.14;
let r  <- 2.0;
let area <- pi * r * r;
let big <- area > 10.0 && r != 0.0;
emit big;
```

**Expected token output:**

```
KW_LET
IDENT("pi")
ASSIGN
FLOAT_LIT("3.14")
SEMICOLON
KW_LET
IDENT("r")
ASSIGN
FLOAT_LIT("2.0")
SEMICOLON
KW_LET
IDENT("area")
ASSIGN
IDENT("pi")
TIMES
IDENT("r")
TIMES
IDENT("r")
SEMICOLON
KW_LET
IDENT("big")
ASSIGN
IDENT("area")
GT
FLOAT_LIT("10.0")
AND
IDENT("r")
NEQ
FLOAT_LIT("0.0")
SEMICOLON
KW_EMIT
IDENT("big")
SEMICOLON
```

---

### ✅ Test File 7 — `comments_only.pico`

```pico
-- This file has only comments
-- No tokens should be produced
-- Every line is a comment
```

**Expected token output:**

```
(no tokens — empty output)
```

---

## Source Files That Should FAIL Lexing

### ❌ Error File 1 — `bad_string.pico`

```pico
-- String that is never closed
let msg <- "hello world;
emit msg;
```

**Expected error:**

```
LEXICAL ERROR at line 2: Unexpected character sequence — unterminated string literal starting with '"'
```

**Reason:** The string `"hello world` is never closed before the newline. A newline inside a string literal is not allowed per the `str_char` rule.

---

### ❌ Error File 2 — `invalid_char.pico`

```pico
-- Uses characters not in the PICO alphabet
let x <- 5;
let y <- x @ 3;
```

**Expected error:**

```
LEXICAL ERROR at line 3: Unrecognized character '@'
```

**Reason:** `@` is not defined in any rule of the YALex specification.

---

### ❌ Error File 3 — `bad_number.pico`

```pico
-- Malformed float (trailing dot, no digits after decimal)
let pi <- 3.;
emit pi;
```

**Expected error:**

```
LEXICAL ERROR at line 2: Unrecognized token '3.' — float requires digits after the decimal point
```

**Reason:** The `float_lit` rule requires `digit+` after the `.`, so `3.` is not a valid token. The lexer matches `3` as `INT_LIT`, then encounters `.` which does not match any rule as a standalone token.

---

### ❌ Error File 4 — `hash_comment.pico`

```pico
# This uses Python-style comments which PICO does not support
let x <- 1;
emit x;
```

**Expected error:**

```
LEXICAL ERROR at line 1: Unrecognized character '#'
```

**Reason:** PICO only supports `--` line comments. The `#` character is not defined in any rule.

---

### ❌ Error File 5 — `bad_assign.pico`

```pico
-- Wrong assignment operator (uses = instead of <-)
let x = 10;
emit x;
```

**Expected error:**

```
LEXICAL ERROR at line 2: Unrecognized character '='
```

**Reason:** PICO uses `<-` for assignment and `==` for equality. A standalone `=` does not match any rule.

---

### ❌ Error File 6 — `unclosed_block.pico`

```pico
-- Note: This is a LEXICAL file — the lexer itself will tokenize fine
-- but it is included to show a file with a character PICO cannot lex
when (true) {
    emit "open";
    let x <- 99 $ 2;
}
```

**Expected error:**

```
LEXICAL ERROR at line 4: Unrecognized character '$'
```

**Reason:** `$` is not in the PICO alphabet and has no matching rule.

---

## Summary Table

| File                    | Result  | Reason                                           |
|-------------------------|---------|--------------------------------------------------|
| `hello.pico`            | ✅ PASS  | Valid tokens only                                |
| `arithmetic.pico`       | ✅ PASS  | Numbers, operators, parentheses                  |
| `conditional.pico`      | ✅ PASS  | Keywords, braces, comparison operators           |
| `loop.pico`             | ✅ PASS  | Repeat/until, full block                         |
| `macro.pico`            | ✅ PASS  | Macro keyword, comma, nested expression          |
| `floats_and_logic.pico` | ✅ PASS  | Float literals, `&&`, `!=`, `>`                  |
| `comments_only.pico`    | ✅ PASS  | No tokens, skipped entirely                      |
| `bad_string.pico`       | ❌ ERROR | Unterminated string crosses newline              |
| `invalid_char.pico`     | ❌ ERROR | `@` has no matching rule                         |
| `bad_number.pico`       | ❌ ERROR | `3.` is not a valid `float_lit` — no post-digits |
| `hash_comment.pico`     | ❌ ERROR | `#` has no matching rule                         |
| `bad_assign.pico`       | ❌ ERROR | Bare `=` has no matching rule                    |
| `unclosed_block.pico`   | ❌ ERROR | `$` has no matching rule                         |

---

## Notes

1. **Longest match rule**: When the input is `<=`, your lexer must emit `LEQ` (not `LT` followed by `EQ`). The two-character operators must be checked before their single-character prefixes.

2. **Keyword vs. identifier priority**: The words `true`, `false`, `macro`, `emit`, etc. must be matched as keywords before the general `ident` rule fires. In YALex, order of definition under `rule` determines priority on ties — place keywords first.

3. **Float before int**: The rule for `float_lit` must appear before `int_lit` in the rule block. Otherwise the lexer matches `3` as `INT_LIT` and then sees `.14` which starts with an unmatched `.`.

4. **Comment skipping**: `line_cmt` returns `lexbuf` (not a token), causing the lexer to consume the comment and continue. This is the standard idiom for whitespace and comment skipping.

5. **EOF handling**: Always include the `eof` rule last. Failing to handle end-of-file causes the lexer to crash on valid inputs that terminate normally.