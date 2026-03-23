# YALex — Yet Another Lex Generator

Generador de analizadores léxicos que lee especificaciones `.yal` (sintaxis inspirada en ocamllex/Lex) y produce analizadores léxicos en Python autónomos.

**Repositorio:** [github.com/lfmendoza/lexer-generator](https://github.com/lfmendoza/lexer-generator)

## Configuración del entorno

Requisitos comunes: **Python 3.10 o superior** y **Git** (para clonar el repositorio). El proyecto no usa dependencias externas en tiempo de ejecución; solo herramientas de desarrollo en el extra `[dev]`.

### Obtener el código

```bash
git clone https://github.com/lfmendoza/lexer-generator.git
cd lexer-generator
```

Instrucciones por plataforma: **Windows**, **macOS**, **Linux** (Debian/Ubuntu, Fedora y Arch).

### Windows

1. Instala Python desde [python.org](https://www.python.org/downloads/) (marca “Add python.exe to PATH”) o con `winget install Python.Python.3.12`.
2. Abre una terminal (PowerShell o **cmd**) en la carpeta del proyecto.
3. Crea y activa un entorno virtual:

   ```powershell
   py -3 -m venv .venv
   .venv\Scripts\activate
   ```

4. Actualiza pip e instala el proyecto en modo editable:

   ```powershell
   python -m pip install -U pip
   pip install -e ".[dev]"
   ```

5. Comprueba la instalación: `yalex --help` o `python -m yalex --help`. Sin activar el venv también puedes usar `python yalex_cli.py --help` (añade `src/` al path automáticamente).

6. **Graphviz** (opcional, para convertir `.dot` a PNG): [Instalador](https://graphviz.org/download/) o `winget install Graphviz.Graphviz`. Asegúrate de que `dot` esté en el `PATH`.

7. **Make** no viene por defecto; para `make check` usa [Git for Windows](https://git-scm.com/) (incluye Git Bash con `make` en algunos entornos), [Chocolatey](https://chocolatey.org/) (`choco install make`), o ejecuta a mano los comandos indicados en [Desarrollo](#desarrollo).

### macOS

1. Instala Python con [python.org](https://www.python.org/downloads/macos/) o Homebrew: `brew install python@3.12`.
2. En la carpeta del proyecto:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -U pip
   pip install -e ".[dev]"
   ```

3. Graphviz opcional: `brew install graphviz`.

4. `make` suele estar disponible con las herramientas de línea de comandos de Xcode (`xcode-select --install`).

### Linux (Debian / Ubuntu y derivados)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip graphviz build-essential
cd /ruta/al/lexer-generator
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

### Linux (Fedora)

```bash
sudo dnf install -y python3 python3-pip graphviz gcc
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

### Linux (Arch)

```bash
sudo pacman -S python python-pip graphviz base-devel
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

### Comprobar que todo funciona

Con el entorno virtual activado, en la raíz del repositorio:

```bash
pytest tests/ -q
python yalex_cli.py specs/yal/arithmetic_expression.yal -o _test_lexer --no-trees --no-dfa-graph -q
```

Opcional: `pre-commit install` para ejecutar Ruff al hacer commit (requiere el extra `[dev]` ya instalado).

## Estructura del proyecto

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

Tras [configurar el entorno](#configuración-del-entorno), ejecuta: `yalex`, `python -m yalex` o `python yalex_cli.py`.

## Funcionamiento

La canalización sigue la teoría habitual de construcción de compiladores:

1. **Análisis del `.yal`** — cabecera, definiciones `let`, patrones y acciones de `rule`, y cola (trailer)
2. **Análisis de cada regex** — la sintaxis regex de YALex se convierte en un AST
3. **Construcción de AFN** — construcción de Thompson por cada patrón de regla
4. **AFN unificado** — se enlazan los AFN de las reglas con transiciones épsilon desde un super-estado inicial
5. **Conversión a AFD** — construcción por subconjuntos
6. **Minimización del AFD** — refinamiento de particiones (estilo Hopcroft)
7. **Generación del lexer** — archivo Python con la tabla de transiciones del AFD
8. **Visualización** — archivos DOT (Graphviz) para árboles de expresiones y el AFD

## Uso

### Paso 1: generar un lexer a partir de un `.yal`

```bash
yalex specs/yal/arithmetic_expression.yal -o my_lexer
# o: python yalex_cli.py specs/yal/arithmetic_expression.yal -o my_lexer
```

Se generan `my_lexer.py`, `my_lexer_trees/` (DOT de los árboles de regex) y `my_lexer_dfa.dot`.

Segundo ejemplo (lenguaje imperativo):

```bash
yalex specs/yal/imperative_core.yal -o imp_lexer
python imp_lexer.py samples/inputs/imperative_core_sample.txt
```

### Paso 2: ejecutar el lexer generado

```bash
python my_lexer.py samples/inputs/arithmetic_expressions.txt
```

Salida de ejemplo:

```
=== TOKENS ===
('ID', 'x', 1, 1)
('ASSIGN', '=', 1, 3)
('NUMBER', 3, 1, 5)
('PLUS', '+', 1, 7)
('NUMBER', 42, 1, 9)
...
```

### Opcional: convertir DOT a imágenes

Si tienes Graphviz instalado:

```bash
dot -Tpng my_lexer_dfa.dot -o my_lexer_dfa.png
dot -Tpng my_lexer_trees/combined.dot -o combined_tree.png
```

## Opciones de línea de comandos

| Opción | Descripción |
|--------|---------------|
| `-o NOMBRE` | Prefijo de salida (sin extensión `.py`) |
| `--no-trees` | No generar DOT de árboles de expresiones |
| `--no-dfa-graph` | No generar el diagrama DOT del AFD |
| `-v` / `--verbose` | Registro detallado |
| `-q` / `--quiet` | Salida mínima (oculta líneas `[INFO]` de codegen/DOT) |
| `--trace human` / `json` / `off` | Trazas del pipeline (por defecto: `off`) |

## Referencia de sintaxis YALex

### Estructura del archivo

```
(* comentarios *)
{ cabecera opcional en Python }
let nombre = regex
...
rule punto_de_entrada =
    patron   { accion }
  | patron   { accion }
  ...
{ cola opcional en Python }
```

### Sintaxis de expresiones regulares

| Sintaxis | Significado |
|----------|-------------|
| `'c'` | Literal de un carácter |
| `'\n'` | Secuencia de escape |
| `_` | Cualquier carácter |
| `"abc"` | Cadena (concatenación de caracteres) |
| `['a'-'z']` | Clase de caracteres con rango |
| `['a' 'b' 'c']` | Clase de caracteres (conjunto) |
| `[^'0'-'9']` | Clase negada |
| `r1 \| r2` | Unión (alternancia) |
| `r1 r2` | Concatenación |
| `r*` | Estrella de Kleene |
| `r+` | Cierre positivo |
| `r?` | Opcional |
| `r1 # r2` | Diferencia de conjuntos |
| `(r)` | Agrupación |
| `eof` | Fin de archivo |
| `ident` | Referencia a una definición `let` |

### Precedencia de operadores (de mayor a menor)

1. `#` (diferencia de conjuntos)
2. `*`, `+`, `?`
3. Concatenación
4. `|` (unión)

### Acciones

Las acciones son bloques de código Python entre `{ }`. Variables disponibles:

- `lxm` — lexema coincidente (cadena)
- `lexeme` — igual que `lxm`
- `line` — número de línea donde empieza la coincidencia
- `col` — columna donde empieza la coincidencia
- `lexbuf` — referencia al objeto `Lexer`

Devolver `None` omite el token (p. ej. espacios). Cualquier otro valor se emite como token.

## Comportamiento

Canalización: AST de regex → AFN (Thompson) → AFN combinado → AFD (subconjuntos) → minimización (Hopcroft) → lexer emitido. La coincidencia es de **prefijo más largo**; a igual longitud, gana la regla que aparece antes en la especificación.

Evite el nombre de regla `tokens` como punto de entrada (`rule tokens =`): en el código generado entra en conflicto con el atributo `Lexer.tokens` (lista). Use por ejemplo `gettoken`, `tokenize`, etc.

El proyecto y el código que genera YALex solo usan la biblioteca estándar de Python.

## Requisitos

- Python 3.10 o superior
- Graphviz (opcional, para convertir DOT a PNG)

## Desarrollo

```bash
make install
make check
pre-commit install
```

Sin `make` (p. ej. Windows): `pip install -e ".[dev]"`, luego `ruff check src tests yalex_cli.py`, `mypy src/yalex`, `pytest`.

## Información del curso

CC3071 — Diseño de Lenguajes de Programación  
Universidad del Valle de Guatemala  
Facultad de Ingeniería — Departamento de Ciencia de la Computación
