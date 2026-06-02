# ArnoldC — YALex Lexer Specification & Test Suite

Implementación: [`specs/yal/arnoldc.yal`](yal/arnoldc.yal). Ejemplos: [`samples/inputs/arnoldc/`](../samples/inputs/arnoldc/).

## Overview

**ArnoldC** is an esoteric imperative programming language created by Lauri Hartikka where every keyword is a famous Arnold Schwarzenegger movie quote. It supports variables (integers only), arithmetic, logical operations, conditionals, while loops, and methods.

This document provides the complete YALex specification for lexing ArnoldC source files, along with valid and invalid test inputs with expected outputs.

---

## ArnoldC Token Reference

| Token Name              | Lexeme                                          | Origin / Meaning              |
|-------------------------|-------------------------------------------------|-------------------------------|
| `KW_MAIN_START`         | `IT'S SHOWTIME`                                 | Start of main method          |
| `KW_MAIN_END`           | `YOU HAVE BEEN TERMINATED`                      | End of main method            |
| `KW_PRINT`              | `TALK TO THE HAND`                              | Print statement               |
| `KW_DECLARE`            | `HEY CHRISTMAS TREE`                            | Variable declaration          |
| `KW_INIT`               | `YOU SET US UP`                                 | Initial value for declaration |
| `KW_ASSIGN_START`       | `GET TO THE CHOPPER`                            | Begin assignment block        |
| `KW_ASSIGN_INIT`        | `HERE IS MY INVITATION`                         | Set stack value               |
| `KW_ASSIGN_END`         | `ENOUGH TALK`                                   | End assignment block          |
| `KW_PLUS`               | `GET UP`                                        | Arithmetic add                |
| `KW_MINUS`              | `GET DOWN`                                      | Arithmetic subtract           |
| `KW_TIMES`              | `YOU'RE FIRED`                                  | Arithmetic multiply           |
| `KW_DIV`                | `HE HAD TO SPLIT`                               | Arithmetic divide             |
| `KW_EQ`                 | `YOU ARE NOT YOU YOU ARE ME`                    | Logical equal                 |
| `KW_GT`                 | `LET OFF SOME STEAM BENNET`                     | Logical greater than          |
| `KW_OR`                 | `CONSIDER THAT A DIVORCE`                       | Logical or                    |
| `KW_AND`                | `KNOCK KNOCK`                                   | Logical and                   |
| `KW_IF`                 | `BECAUSE I'M GOING TO SAY PLEASE`               | If condition                  |
| `KW_ELSE`               | `BULLSHIT`                                      | Else branch                   |
| `KW_ENDIF`              | `YOU HAVE NO RESPECT FOR LOGIC`                 | End of if block               |
| `KW_WHILE`              | `STICK AROUND`                                  | While loop start              |
| `KW_ENDWHILE`           | `CHILL`                                         | While loop end                |
| `KW_METHOD_DEF`         | `LISTEN TO ME VERY CAREFULLY`                   | Method definition             |
| `KW_METHOD_ARG`         | `I NEED YOUR CLOTHES YOUR BOOTS AND YOUR MOTORCYCLE` | Method argument          |
| `KW_METHOD_NONVOID`     | `GIVE THESE PEOPLE AIR`                         | Marks method as non-void      |
| `KW_METHOD_END`         | `HASTA LA VISTA, BABY`                          | End of method                 |
| `KW_RETURN`             | `I'LL BE BACK`                                  | Return statement              |
| `KW_CALL_VOID`          | `DO IT NOW`                                     | Call a void method            |
| `KW_CALL_ASSIGN`        | `GET YOUR ASS TO MARS`                          | Assign result of method call  |
| `KW_FALSE`              | `@I LIED`                                       | Integer constant 0            |
| `KW_TRUE`               | `@NO PROBLEMO`                                  | Integer constant 1            |
| `INT_LIT`               | sequence of digits, optionally negative         | Integer literal               |
| `STRING_LIT`            | `"..."` double-quoted string                    | String literal                |
| `IDENT`                 | lowercase identifier                            | Variable or method name       |

> **Whitespace** between tokens (spaces, newlines, tabs) is consumed and produces no tokens.  
> ArnoldC has **no comment syntax** — every line is either a keyword, a value, or an identifier.

---

## Critical Lexing Notes

ArnoldC's keywords are **multi-word phrases**, some containing apostrophes, commas, and `@` symbols. This creates several important challenges for your lexer:

1. **Multi-word keywords must be matched as atomic units.** `TALK TO THE HAND` is a single token, not four. Use string literals in YALex (e.g., `"TALK TO THE HAND"`) for each keyword.

2. **Longest match is critical.** `YOU HAVE BEEN TERMINATED` and `YOU HAVE NO RESPECT FOR LOGIC` both start with `YOU`. The lexer must match the longer phrase when applicable — but since these appear on their own lines, newline-delimited reading is the natural strategy.

3. **Apostrophes in keywords** (`IT'S SHOWTIME`, `YOU'RE FIRED`, `I'LL BE BACK`, `I'M GOING TO SAY PLEASE`) must be included literally in the string match rules.

4. **`@` prefix** on `@I LIED` and `@NO PROBLEMO` makes them distinct from identifiers and must be handled explicitly.

5. **IDENT is lowercase-only.** Variable names in ArnoldC are always lowercase; keywords are always UPPERCASE. This makes disambiguation straightforward.

---

## YALex Specification File

```
(* arnoldc.yal — YALex specification for the ArnoldC language *)

{
(* Generated lexer for ArnoldC — Arnold Schwarzenegger keyword language *)
(* All keywords are exact multi-word phrases, matched as string literals  *)
}

(* ── Character classes ──────────────────────────────── *)

let digit     = ['0'-'9']
let lower     = ['a'-'z']
let upper     = ['A'-'Z']
let ident     = lower (lower | digit | '_')*

(* ── Integer literals (may be negative) ─────────────── *)

let int_lit   = '-'? digit+

(* ── String literal (double-quoted, no embedded newlines) *)

let str_char  = [^ '"' '\n' '\\'] | '\\' _
let str_lit   = '"' str_char* '"'

(* ══════════════════════════════════════════════════════ *)

rule gettoken =

    (* Skip whitespace and newlines *)
    [' ' '\t' '\n' '\r']                                      { return lexbuf }

    (* ── Boolean / constant macros ── must come BEFORE ident ── *)

  | "@NO PROBLEMO"                                            { return KW_TRUE }
  | "@I LIED"                                                 { return KW_FALSE }

    (* ── Main method delimiters ── *)

  | "IT'S SHOWTIME"                                           { return KW_MAIN_START }
  | "YOU HAVE BEEN TERMINATED"                                { return KW_MAIN_END }

    (* ── Print ── *)

  | "TALK TO THE HAND"                                        { return KW_PRINT }

    (* ── Variable declaration ── *)

  | "HEY CHRISTMAS TREE"                                      { return KW_DECLARE }
  | "YOU SET US UP"                                           { return KW_INIT }

    (* ── Assignment block ── *)

  | "GET TO THE CHOPPER"                                      { return KW_ASSIGN_START }
  | "HERE IS MY INVITATION"                                   { return KW_ASSIGN_INIT }
  | "ENOUGH TALK"                                             { return KW_ASSIGN_END }

    (* ── Arithmetic operations ── *)

  | "GET UP"                                                  { return KW_PLUS }
  | "GET DOWN"                                                { return KW_MINUS }
  | "YOU'RE FIRED"                                            { return KW_TIMES }
  | "HE HAD TO SPLIT"                                         { return KW_DIV }

    (* ── Logical operations ── *)

  | "YOU ARE NOT YOU YOU ARE ME"                              { return KW_EQ }
  | "LET OFF SOME STEAM BENNET"                               { return KW_GT }
  | "CONSIDER THAT A DIVORCE"                                 { return KW_OR }
  | "KNOCK KNOCK"                                             { return KW_AND }

    (* ── Conditionals ── must check longer phrases first ── *)

  | "BECAUSE I'M GOING TO SAY PLEASE"                         { return KW_IF }
  | "BULLSHIT"                                                { return KW_ELSE }
  | "YOU HAVE NO RESPECT FOR LOGIC"                           { return KW_ENDIF }

    (* ── While loop ── *)

  | "STICK AROUND"                                            { return KW_WHILE }
  | "CHILL"                                                   { return KW_ENDWHILE }

    (* ── Methods ── longest phrases first ── *)

  | "LISTEN TO ME VERY CAREFULLY"                             { return KW_METHOD_DEF }
  | "I NEED YOUR CLOTHES YOUR BOOTS AND YOUR MOTORCYCLE"      { return KW_METHOD_ARG }
  | "GIVE THESE PEOPLE AIR"                                   { return KW_METHOD_NONVOID }
  | "HASTA LA VISTA, BABY"                                    { return KW_METHOD_END }
  | "I'LL BE BACK"                                            { return KW_RETURN }
  | "GET YOUR ASS TO MARS"                                    { return KW_CALL_ASSIGN }
  | "DO IT NOW"                                               { return KW_CALL_VOID }

    (* ── Literals and identifiers ── last, after all keywords ── *)

  | str_lit                                                   { return STRING_LIT(lxm) }
  | int_lit                                                   { return INT_LIT(lxm) }
  | ident                                                     { return IDENT(lxm) }

    (* ── End of file ── *)

  | eof                                                       { raise( 'End of input' ) }
```

---

## Source Files That SHOULD Be Lexed Successfully

### ✅ Test File 1 — `hello.arnoldc`

```arnoldc
IT'S SHOWTIME
TALK TO THE HAND "Hello, World!"
YOU HAVE BEEN TERMINATED
```

**Expected token output:**

```
KW_MAIN_START
KW_PRINT
STRING_LIT("\"Hello, World!\"")
KW_MAIN_END
```

---

### ✅ Test File 2 — `variables.arnoldc`

```arnoldc
IT'S SHOWTIME
HEY CHRISTMAS TREE x
YOU SET US UP 5
HEY CHRISTMAS TREE y
YOU SET US UP 10
TALK TO THE HAND x
TALK TO THE HAND y
YOU HAVE BEEN TERMINATED
```

**Expected token output:**

```
KW_MAIN_START
KW_DECLARE
IDENT("x")
KW_INIT
INT_LIT("5")
KW_DECLARE
IDENT("y")
KW_INIT
INT_LIT("10")
KW_PRINT
IDENT("x")
KW_PRINT
IDENT("y")
KW_MAIN_END
```

---

### ✅ Test File 3 — `arithmetic.arnoldc`

```arnoldc
IT'S SHOWTIME
HEY CHRISTMAS TREE a
YOU SET US UP 4
HEY CHRISTMAS TREE b
YOU SET US UP 0
GET TO THE CHOPPER b
HERE IS MY INVITATION 4
GET UP a
YOU'RE FIRED 2
ENOUGH TALK
TALK TO THE HAND b
YOU HAVE BEEN TERMINATED
```

*This computes `b = (4 + a) * 2`*

**Expected token output:**

```
KW_MAIN_START
KW_DECLARE
IDENT("a")
KW_INIT
INT_LIT("4")
KW_DECLARE
IDENT("b")
KW_INIT
INT_LIT("0")
KW_ASSIGN_START
IDENT("b")
KW_ASSIGN_INIT
INT_LIT("4")
KW_PLUS
IDENT("a")
KW_TIMES
INT_LIT("2")
KW_ASSIGN_END
KW_PRINT
IDENT("b")
KW_MAIN_END
```

---

### ✅ Test File 4 — `conditional.arnoldc`

```arnoldc
IT'S SHOWTIME
HEY CHRISTMAS TREE score
YOU SET US UP 7
BECAUSE I'M GOING TO SAY PLEASE score
TALK TO THE HAND "Passed"
BULLSHIT
TALK TO THE HAND "Failed"
YOU HAVE NO RESPECT FOR LOGIC
YOU HAVE BEEN TERMINATED
```

**Expected token output:**

```
KW_MAIN_START
KW_DECLARE
IDENT("score")
KW_INIT
INT_LIT("7")
KW_IF
IDENT("score")
KW_PRINT
STRING_LIT("\"Passed\"")
KW_ELSE
KW_PRINT
STRING_LIT("\"Failed\"")
KW_ENDIF
KW_MAIN_END
```

---

### ✅ Test File 5 — `while_loop.arnoldc`

```arnoldc
IT'S SHOWTIME
HEY CHRISTMAS TREE running
YOU SET US UP @NO PROBLEMO
HEY CHRISTMAS TREE n
YOU SET US UP 0
STICK AROUND running
GET TO THE CHOPPER n
HERE IS MY INVITATION n
GET UP 1
ENOUGH TALK
TALK TO THE HAND n
GET TO THE CHOPPER running
HERE IS MY INVITATION 5
LET OFF SOME STEAM BENNET n
ENOUGH TALK
CHILL
YOU HAVE BEEN TERMINATED
```

*This prints 1 through 5.*

**Expected token output:**

```
KW_MAIN_START
KW_DECLARE
IDENT("running")
KW_INIT
KW_TRUE
KW_DECLARE
IDENT("n")
KW_INIT
INT_LIT("0")
KW_WHILE
IDENT("running")
KW_ASSIGN_START
IDENT("n")
KW_ASSIGN_INIT
IDENT("n")
KW_PLUS
INT_LIT("1")
KW_ASSIGN_END
KW_PRINT
IDENT("n")
KW_ASSIGN_START
IDENT("running")
KW_ASSIGN_INIT
INT_LIT("5")
KW_GT
IDENT("n")
KW_ASSIGN_END
KW_ENDWHILE
KW_MAIN_END
```

---

### ✅ Test File 6 — `method.arnoldc`

```arnoldc
IT'S SHOWTIME
HEY CHRISTMAS TREE result
YOU SET US UP 0
GET YOUR ASS TO MARS result
DO IT NOW double 21
TALK TO THE HAND result
YOU HAVE BEEN TERMINATED

LISTEN TO ME VERY CAREFULLY double
I NEED YOUR CLOTHES YOUR BOOTS AND YOUR MOTORCYCLE val
GIVE THESE PEOPLE AIR
HEY CHRISTMAS TREE out
YOU SET US UP 0
GET TO THE CHOPPER out
HERE IS MY INVITATION val
YOU'RE FIRED 2
ENOUGH TALK
I'LL BE BACK out
HASTA LA VISTA, BABY
```

**Expected token output:**

```
KW_MAIN_START
KW_DECLARE
IDENT("result")
KW_INIT
INT_LIT("0")
KW_CALL_ASSIGN
IDENT("result")
KW_CALL_VOID
IDENT("double")
INT_LIT("21")
KW_PRINT
IDENT("result")
KW_MAIN_END
KW_METHOD_DEF
IDENT("double")
KW_METHOD_ARG
IDENT("val")
KW_METHOD_NONVOID
KW_DECLARE
IDENT("out")
KW_INIT
INT_LIT("0")
KW_ASSIGN_START
IDENT("out")
KW_ASSIGN_INIT
IDENT("val")
KW_TIMES
INT_LIT("2")
KW_ASSIGN_END
KW_RETURN
IDENT("out")
KW_METHOD_END
```

---

### ✅ Test File 7 — `logic.arnoldc`

```arnoldc
IT'S SHOWTIME
HEY CHRISTMAS TREE a
YOU SET US UP @NO PROBLEMO
HEY CHRISTMAS TREE b
YOU SET US UP @I LIED
HEY CHRISTMAS TREE c
YOU SET US UP 0
GET TO THE CHOPPER c
HERE IS MY INVITATION a
CONSIDER THAT A DIVORCE b
KNOCK KNOCK a
ENOUGH TALK
TALK TO THE HAND c
YOU HAVE BEEN TERMINATED
```

*Tests `@NO PROBLEMO`, `@I LIED`, `CONSIDER THAT A DIVORCE` (OR), and `KNOCK KNOCK` (AND).*

**Expected token output:**

```
KW_MAIN_START
KW_DECLARE
IDENT("a")
KW_INIT
KW_TRUE
KW_DECLARE
IDENT("b")
KW_INIT
KW_FALSE
KW_DECLARE
IDENT("c")
KW_INIT
INT_LIT("0")
KW_ASSIGN_START
IDENT("c")
KW_ASSIGN_INIT
IDENT("a")
KW_OR
IDENT("b")
KW_AND
IDENT("a")
KW_ASSIGN_END
KW_PRINT
IDENT("c")
KW_MAIN_END
```

---

### ✅ Test File 8 — `negative_int.arnoldc`

```arnoldc
IT'S SHOWTIME
HEY CHRISTMAS TREE debt
YOU SET US UP -42
TALK TO THE HAND debt
YOU HAVE BEEN TERMINATED
```

**Expected token output:**

```
KW_MAIN_START
KW_DECLARE
IDENT("debt")
KW_INIT
INT_LIT("-42")
KW_PRINT
IDENT("debt")
KW_MAIN_END
```

---

## Source Files That Should FAIL Lexing

### ❌ Error File 1 — `lowercase_keyword.arnoldc`

```arnoldc
it's showtime
TALK TO THE HAND "hi"
YOU HAVE BEEN TERMINATED
```

**Expected error:**

```
LEXICAL ERROR at line 1: Unrecognized token "it's" — ArnoldC keywords are UPPERCASE only
```

**Reason:** The lexer has no rule matching lowercase `it's`. After whitespace is consumed, `i` begins an `ident` match — but `it's` (with apostrophe) does not match the `ident` rule either (`'` is not in `lower | digit | '_'`). The lexer fails on `'`.

---

### ❌ Error File 2 — `bad_string.arnoldc`

```arnoldc
IT'S SHOWTIME
TALK TO THE HAND "this string never ends
YOU HAVE BEEN TERMINATED
```

**Expected error:**

```
LEXICAL ERROR at line 2: Unterminated string literal — newline encountered inside string
```

**Reason:** `str_char` excludes `\n`, so the string rule fails when the lexer hits the newline before finding a closing `"`.

---

### ❌ Error File 3 — `wrong_macro.arnoldc`

```arnoldc
IT'S SHOWTIME
HEY CHRISTMAS TREE flag
YOU SET US UP @TRUE
YOU HAVE BEEN TERMINATED
```

**Expected error:**

```
LEXICAL ERROR at line 3: Unrecognized token "@TRUE" — valid macros are @NO PROBLEMO and @I LIED
```

**Reason:** `@TRUE` does not match either `"@NO PROBLEMO"` or `"@I LIED"`. The `@` character has no other matching rule and is not part of `ident`, so the lexer fails on `@`.

---

### ❌ Error File 4 — `mixed_case_keyword.arnoldc`

```arnoldc
IT'S SHOWTIME
Talk To The Hand "mixed case"
YOU HAVE BEEN TERMINATED
```

**Expected error:**

```
LEXICAL ERROR at line 2: Unrecognized token beginning with "Talk" — did you mean "TALK TO THE HAND"?
```

**Reason:** `Talk` begins with an uppercase letter but continues with lowercase, making it neither a keyword (which are all-caps phrases) nor a valid `ident` (which must be all lowercase). The lexer has no rule for mixed-case identifiers.

---

### ❌ Error File 5 — `missing_comma.arnoldc`

```arnoldc
IT'S SHOWTIME
LISTEN TO ME VERY CAREFULLY myfunc
HASTA LA VISTA BABY
YOU HAVE BEEN TERMINATED
```

**Expected error:**

```
LEXICAL ERROR at line 3: Unrecognized phrase "HASTA LA VISTA BABY" — keyword is "HASTA LA VISTA, BABY" (comma required)
```

**Reason:** The method-end keyword is exactly `"HASTA LA VISTA, BABY"` — including the comma. Without the comma, this phrase does not match any rule. The lexer will match `HASTA` as a potential start of a longer token but ultimately fail because no rule accepts this exact sequence.

---

### ❌ Error File 6 — `symbol_in_ident.arnoldc`

```arnoldc
IT'S SHOWTIME
HEY CHRISTMAS TREE my-var
YOU SET US UP 1
YOU HAVE BEEN TERMINATED
```

**Expected error:**

```
LEXICAL ERROR at line 2: Unrecognized character '-' following identifier "my"
```

**Reason:** The `ident` rule is `lower (lower | digit | '_')*`. A hyphen `-` is not in this set. The lexer matches `my` as a valid `IDENT`, then encounters `-` which only matches as the start of a negative `int_lit`. However `var` following it would then not complete a valid number, causing a cascading error.

---

### ❌ Error File 7 — `hash_comment.arnoldc`

```arnoldc
IT'S SHOWTIME
# This is not a valid comment in ArnoldC
TALK TO THE HAND "test"
YOU HAVE BEEN TERMINATED
```

**Expected error:**

```
LEXICAL ERROR at line 2: Unrecognized character '#' — ArnoldC has no comment syntax
```

**Reason:** ArnoldC has no comment syntax whatsoever. The `#` character has no matching rule and causes an immediate lexical error.

---

## Summary Table

| File                       | Result  | Reason                                                         |
|----------------------------|---------|----------------------------------------------------------------|
| `hello.arnoldc`            | ✅ PASS  | Simplest valid program                                         |
| `variables.arnoldc`        | ✅ PASS  | Declaration and print tokens                                   |
| `arithmetic.arnoldc`       | ✅ PASS  | Full assignment block with arithmetic ops                      |
| `conditional.arnoldc`      | ✅ PASS  | If/else/endif structure                                        |
| `while_loop.arnoldc`       | ✅ PASS  | While loop with `@NO PROBLEMO` macro                           |
| `method.arnoldc`           | ✅ PASS  | Non-void method, argument, return                              |
| `logic.arnoldc`            | ✅ PASS  | `@I LIED`, `@NO PROBLEMO`, OR, AND operations                  |
| `negative_int.arnoldc`     | ✅ PASS  | Negative integer literal `-42`                                 |
| `lowercase_keyword.arnoldc`| ❌ ERROR | Keywords must be UPPERCASE; lowercase fails `ident` too        |
| `bad_string.arnoldc`       | ❌ ERROR | Unterminated string literal crosses newline                    |
| `wrong_macro.arnoldc`      | ❌ ERROR | `@TRUE` is not a valid macro; only `@NO PROBLEMO` / `@I LIED` |
| `mixed_case_keyword.arnoldc`| ❌ ERROR | `Talk` is neither a keyword nor a valid `ident`               |
| `missing_comma.arnoldc`    | ❌ ERROR | `HASTA LA VISTA BABY` without comma doesn't match any rule     |
| `symbol_in_ident.arnoldc`  | ❌ ERROR | Hyphen `-` not valid in identifiers                            |
| `hash_comment.arnoldc`     | ❌ ERROR | `#` not defined; ArnoldC has zero comment syntax               |

---

## Notes

1. **Multi-word keywords as atomic tokens.** Unlike PICO where every token was a single word or symbol, ArnoldC requires matching entire sentences. Use quoted string literals in YALex (`"GET TO THE CHOPPER"`) — the underlying regex is just a concatenation of character literals. This tests whether your lexer engine correctly handles long string matches.

2. **Ordering still matters for shared prefixes.** `GET UP`, `GET DOWN`, and `GET TO THE CHOPPER` all start with `GET`. Your rule ordering must ensure the longer phrases are tried first (or that your DFA correctly picks the longest match). In YALex, the first matching rule wins on ties — so list longer phrases before shorter ones that share a prefix.

3. **`@` is a keyword prefix, not an operator.** The macros `@I LIED` and `@NO PROBLEMO` are the only tokens in ArnoldC that start with `@`. There is no standalone `@` token. Your lexer must match these as complete units.

4. **Apostrophes are part of keywords.** `IT'S`, `YOU'RE`, `I'LL`, and `I'M` are all embedded in keywords. Your lexer must include them in the string literal rules — they are not special characters in YALex string matching.

5. **No comment syntax means 100% coverage.** Every line in a valid ArnoldC file must be lexable. There is no escape hatch for unknown characters. This is a useful stress-test: any character not covered by your rules will cause a hard failure, so your test suite can verify completeness.

6. **`YOU HAVE BEEN TERMINATED` vs `YOU HAVE NO RESPECT FOR LOGIC`.** Both start with `YOU HAVE`. On a well-implemented maximal-munch DFA this is handled correctly. On a naive rule-ordered lexer, make sure `YOU HAVE NO RESPECT FOR LOGIC` appears before any shorter `YOU HAVE ...` prefix in your rule list.

7. **Identifiers are lowercase-only by design.** This is what makes keyword disambiguation easy in ArnoldC — no identifier will ever be confused with a keyword since all keywords are UPPERCASE. Your `ident` rule can safely be restricted to `['a'-'z']` starts without risk.