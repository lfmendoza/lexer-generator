# Muestras de entrada

Fuentes de prueba por especificación `.yal`. Cubren operadores, literales, comentarios, palabras reservadas vs identificadores y entradas largas.

| `.yal` | Rutas |
|--------|--------|
| `arithmetic_expression.yal` | `inputs/arithmetic_*.txt` |
| `imperative_core.yal` | `inputs/imperative_*.txt` |
| `pico.yal` | `inputs/pico/*.pico` (excepto `invalid_char.pico` en tests de éxito) |
| `arnoldc.yal` | `inputs/arnoldc/*.arnoldc` |

```bash
python <prefijo>.py samples/inputs/...
```

`pytest tests/test_sample_corpus.py` recorre el corpus de éxito; `tests/test_core_lexer_semantics.py` cubre propiedades del motor.
