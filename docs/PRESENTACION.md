# Guion de presentación — YALex (generador de analizadores léxicos)

Guion para presentar YALex: fases, teoría breve y demo con tokens / `--pretty`.

**Duración:** ~8–12 min (recortar *opcional*).

Cada sección incluye **En pantalla / consola**. Raíz del repo; ejemplo con `-o my_lexer`; sin `yalex` en PATH: `python -m yalex`.

| Sección | Dónde mirar (resumen) |
|---------|------------------------|
| 1 | Presentación / título; aún sin demo técnica. |
| 2 | Archivo `.yal` abierto en el editor. |
| 3 | Terminal: `yalex` → luego `python my_lexer.py` sin `--pretty`. |
| 4 | Imagen o `.dot` del AFD; opcional fragmento del `.py` generado. |
| 5 | Carpeta `my_lexer_trees/` y `combined.dot` o PNG del árbol. |
| 6 | Mismo lexer; terminal con `--pretty`. |
| 7 | Misma salida de tokens; solo discurso (léxico vs sintáctico). |
| 8 | Terminal: `yalex` con `--trace human`. |
| 9 | Cierre: opcional split `.yal` + salida `--pretty`. |

---

## 1. Gancho (30–45 s)

> “Cuando escribimos el front-end de un compilador o de un intérprete, lo primero que necesitamos es **dividir el texto fuente en piezas con significado**: números, nombres, operadores, palabras reservadas… Eso es el **análisis léxico**. Hacerlo a mano es repetitivo; los **generadores de lexers** permiten describir esos trozos con **expresiones regulares** y obtener un programa que los reconoce automáticamente.”

**En pantalla / consola:** título o README; sin terminal aún.

---

## 2. Qué es YALex en una frase (30 s)

> “**YALex** es una herramienta que lee una **especificación** en archivo `.yal` —patrones tipo lex/ocamllex— y **genera un programa en Python** que analiza texto y devuelve **tokens**. No sustituye al analizador sintáctico completo; se queda en la capa **léxica**.”

**En pantalla / consola:** editor con `specs/yal/arithmetic_expression.yal` (`let`, `rule`, acciones).

---

## 3. Dos programas, dos fases (1–2 min)

**Mensaje clave:** separar **generar** el lexer de **usar** el lexer.

| Fase | Comando típico | Entrada | Salida |
|------|----------------|---------|--------|
| **1** | `yalex archivo.yal -o prefijo` | `.yal` | `prefijo.py` (+ DOT opcional) |
| **2** | `python prefijo.py entrada.txt` | Texto fuente | Lista de tokens |

> “En la **primera fase** no analizamos todavía nuestro lenguaje de usuario: **compilamos la especificación** y construimos las tablas del autómata. En la **segunda fase** ejecutamos el `.py` generado sobre un archivo de ejemplo y vemos los **tokens**.”

*Opcional:* dibujar en pizarra o diapositiva: `.yal` → `yalex` → `.py` → `entrada` → `tokens`.

**En pantalla / consola:** **terminal** en la raíz del proyecto.

1. **Fase 1 — generar el lexer** (deja visible todo el log de `yalex`):

```bash
yalex specs/yal/arithmetic_expression.yal -o my_lexer
```

Deberías ver mensajes del estilo “Parsing…”, “Generating expression trees…”, “Building NFA…”, “Lexer generated…”, y rutas a `my_lexer.py`, `my_lexer_trees/`, `my_lexer_dfa.dot`.

2. **Fase 2 — usar el lexer** (aún **sin** `--pretty`, para enfatizar la lista de tokens “cruda”):

```bash
python my_lexer.py samples/inputs/arithmetic_expressions.txt
```

Señala en pantalla la sección `=== TOKENS ===` y las tuplas `(tipo, valor, línea, columna)`.

---

## 4. Qué hace por dentro (teoría del curso) (2–3 min)

Enumerar con calma, enlazando con la asignatura:

1. Parse del `.yal` (reglas `let`, `rule`, acciones en Python).
2. Cada patrón → AST de regex.
3. **Thompson:** regex → AFN.
4. Unión de reglas → AFN global.
5. **Subconjuntos:** AFN → AFD.
6. **Minimización** del AFD.
7. Emisión de código con **tablas** y **acciones** que el usuario escribió.

> “La política de coincidencia es **prefijo más largo**; si dos reglas empatan en longitud, gana la que **aparece antes** en el archivo —eso lo fijamos nosotros en el diseño del `.yal`.”

*Opcional:* mostrar `prefijo_dfa.dot` convertido a PNG con Graphviz.

**En pantalla / consola:** elige **una** de estas opciones (no hace falta las tres):

- **Visor de imágenes / diapositiva:** `my_lexer_dfa.png` (si ya generaste PNG con Graphviz a partir de `my_lexer_dfa.dot`).
- **Editor de texto:** abre `my_lexer_dfa.dot` y muestra las primeras líneas (nodos y transiciones) mientras nombras Thompson → subconjuntos → minimización.
- **Editor:** abre `my_lexer.py` y muestra solo un **fragmento** donde se vean **tablas** o la función principal del analizador (sin leer línea a línea), para conectar “emisión de código” con el pipeline.

Si en la sección 3 **no** generaste aún el lexer, ejecuta antes el comando de la fase 1 de la sección 3.

---

## 5. Árbol de expresión regular (graficado) (1–2 min)

**Qué es:** cada patrón del `.yal` se parsea a un **AST de regex** (concatenación `·`, unión `|`, Kleene `*`, etc.). Ese árbol es la **representación explícita** de la **definición regular** que describe cada **componente léxico** (cada regla `rule` define un **tipo de token** y su patrón). Con `-o my_lexer`, el generador escribe los **DOT** en `my_lexer_trees/` (por defecto; se desactiva con `--no-trees`):

| Archivo | Contenido |
|---------|-----------|
| `def_<nombre>.dot` | AST del `let` con ese nombre |
| `rule_<i>.dot` | AST del patrón de la regla *i* |
| `combined.dot` | unión (`|`) de los patrones de todas las reglas (visión global) |

**Texto listo para diapositiva o guion:**

> **Árbol de expresión** (graficado) que representa la **especificación** —definición regular— de los **componentes léxicos** (**tokens**) definidos en el archivo YALex.
>
> El **programa fuente** que genera la herramienta es el que **implementa el analizador léxico** a partir de esa especificación; al ejecutarlo sobre un archivo de entrada se obtiene la secuencia de tokens.

**Cómo mostrarlo en pantalla (PNG):** con [Graphviz](https://graphviz.org/) instalado y en el `PATH`, al ejecutar `yalex` se intenta generar también `*.png` junto a cada `.dot`. Si no aparecen, convierte a mano:

```bash
dot -Tpng my_lexer_trees/combined.dot -o combined_tree.png
dot -Tpng my_lexer_trees/def_digit.dot -o def_digit.png
```

Abre el PNG en visor de imágenes o insértalo en la presentación. El título del grafo en la imagen coincide con el nombre del AST (`combined_rules`, `let digit`, `rule_0`, etc.).

**Discurso corto:** “Aquí no vemos todavía el autómata: vemos **cómo está construida la expresión regular** como árbol. Esa misma estructura es la que el compilador interno traduce después a AFN y AFD.”

---

## 6. Salida: tabla de tokens **y** vista “como en el libro” (2–3 min)

**Problema pedagógico:** la tabla de tuplas es correcta pero **poco intuitiva** para ver de un vistazo si `x + y` se clasificó como identificador, más, identificador.

**Solución incluida en el generador:** el programa emitido acepta **`--pretty`**.

Ejemplo de discurso:

> “Además de imprimir `=== TOKENS ===` con las tuplas `(tipo, valor, línea, columna)`, podemos ejecutar:
>
> `python my_lexer.py entrada.txt --pretty`
>
> y obtener una segunda sección, **Vista léxica**, donde **por cada línea** se muestra el **texto original** y la secuencia de **tipos** en forma legible, por ejemplo **Tipos: ID PLUS ID**. Así validamos **visualmente** que el contenido del archivo se tokeniza como esperamos, no solo mirando filas sueltas.”

Demostración en vivo (recomendado):

```bash
python my_lexer.py samples/inputs/arithmetic_expressions.txt --pretty
```

Señalar en pantalla las líneas `Texto:`, `Tipos:` y `Detalle:`.

**En pantalla / consola:** **terminal** con el mismo ejemplo, ahora con **`--pretty`** (es la demo principal de esta sección):

```bash
python my_lexer.py samples/inputs/arithmetic_expressions.txt --pretty
```

Haz **scroll** para que se vean **dos bloques**: primero `=== TOKENS ===` (tuplas), luego **Vista léxica** con `Texto:` / `Tipos:` / `Detalle:`. Contrasta verbalmente “datos en bruto” vs “lectura humana”.

---

## 7. “¿Valida el programa la especificación?” (1 min)

> “Hay que distinguir niveles. **A nivel léxico**, si todo el archivo se tokeniza sin errores y los tipos coinciden con nuestro diseño, el texto **cumple la especificación léxica**. **A nivel sintáctico** —si la secuencia `ID PLUS ID` forma una expresión válida— eso lo resuelve otro módulo, el **parser**, no el lexer. YALex **no** comprueba gramáticas BNF; solo **clasifica caracteres en tokens** según regex.”

**En pantalla / consola:** **no** hace falta un comando nuevo: deja visible la **última salida** de `python my_lexer.py … --pretty` (sección 6) y señala que **no hubo error léxico**. Opcional: mencionar que una cadena “rara” pero tokenizable seguiría siendo válida para el lexer y aun así podría ser inválida para un parser (solo discurso).

---

## 8. Trazas al generar el lexer (1 min)

> “Cuando ejecutamos `yalex`, podemos usar `--trace human` o `--trace json` para ver **hitos del pipeline de compilación**: especificación leída, número de estados del AFD, archivos escritos. Eso sirve para depurar **el generador**, no para trazar carácter a carácter la ejecución del lexer en la entrada —para eso tenemos la **tabla** y la vista **`--pretty`**.”

**En pantalla / consola:** **terminal** — vuelve a ejecutar la **fase 1** con traza (puedes usar otro prefijo para no sobrescribir, o regenerar sobre `my_lexer`):

```bash
yalex specs/yal/arithmetic_expression.yal -o my_lexer --trace human
```

(O `python -m yalex …`.) Haz scroll por los eventos: parseo de la especificación, árboles, estados del AFD, ruta del `.py` generado. Contrasta con la salida del **lexer** sobre el archivo de entrada (eso fue la sección 6, no aquí).

---

## 9. Cierre (30 s)

> “En resumen: YALex **materializa** en código la cadena teoría de compiladores **regex → AFN → AFD → tabla**; nosotros **observamos** el resultado como tabla de tokens y, con `--pretty`, como **texto alineado a tipos**, que es la forma más clara de **convencerse** de que el análisis léxico hace lo que diseñamos.”

Preguntas.

**En pantalla / consola:** **opcional** — pantalla dividida: a un lado `specs/yal/arithmetic_expression.yal` (la especificación), al otro la salida de `python my_lexer.py samples/inputs/arithmetic_expressions.txt --pretty` (el comportamiento observado). Refuerza el mensaje: **especificación → programa generado → tokens**.

---

## Notas para el presentador

- **Proyecto y repositorio:** ver [README.md](../README.md) y sección [Configuración del entorno](../README.md#configuración-del-entorno).
- **Demo:** practicar `yalex` y el `.py` generado; tener una entrada extra para la sesión. Specs: [SPEC.md](../specs/SPEC.md), [SPEC-ARNOLDC.md](../specs/SPEC-ARNOLDC.md).
- **PDF:** repo, arquitectura, pipeline regex → AFN → AFD, uso, límites del lexer.
- **Sin dependencias raras:** solo biblioteca estándar de Python en el generador y en el código generado.
- **Graphviz:** opcional para **imagen** del AFD (`*_dfa.dot`) y de los **árboles de expresión** (`*_lexer_trees/*.dot`); el flujo principal de tokens no lo requiere. Si `dot` no está en el `PATH`, convierte manualmente con los comandos de la sección 5.
