# YALex — Yet Another Lex Generator

Generador de analizadores léxicos que lee especificaciones `.yal` (sintaxis inspirada en ocamllex/Lex) y produce analizadores léxicos en Python autónomos.

**Repositorio:** [github.com/lfmendoza/lexer-generator](https://github.com/lfmendoza/lexer-generator)

## Configuración del entorno

Resumen rápido: instala **Python 3.10+** y **Git**, clona el repositorio, crea un entorno virtual (`.venv`), ejecuta `pip install -e ".[dev]"` y comprueba con `pytest`. El proyecto solo añade dependencias de desarrollo en `[dev]`; el generador y el código que emite usan la biblioteca estándar de Python.

| Sección | Contenido |
|---------|-----------|
| [Requisitos previos](#requisitos-previos) | Qué instalar antes de empezar |
| [Clonar el repositorio](#clonar-el-repositorio) | `git clone` |
| [Windows](#windows) | PowerShell, CMD y Git Bash |
| [macOS](#macos) | Terminal y Homebrew |
| [Linux](#linux) | Debian/Ubuntu, Fedora, Arch |
| [Comprobar la instalación](#comprobar-la-instalación) | Pruebas y herramientas opcionales |

### Requisitos previos

- **Python** 3.10 o superior ([Windows](https://www.python.org/downloads/windows/) · [macOS](https://www.python.org/downloads/macos/) · Linux: gestor de paquetes de la distro).
- **Git**, para clonar [el repositorio](https://github.com/lfmendoza/lexer-generator).

En Windows, al instalar Python desde el instalador oficial, marca **Add python.exe to PATH**. También puedes usar `winget install Python.Python.3.12`.

### Clonar el repositorio

```bash
git clone https://github.com/lfmendoza/lexer-generator.git
cd lexer-generator
```

A partir de aquí, todos los comandos se ejecutan **dentro** de la carpeta `lexer-generator` (raíz del proyecto).

---

### Windows

Instala Python si aún no lo tienes (véase [Requisitos previos](#requisitos-previos)). Luego elige **una** terminal; los tres métodos crean el mismo entorno virtual (`.venv`); solo cambia la forma de activarlo.

#### PowerShell (recomendado)

1. Abre **Windows Terminal → PowerShell** o busca “PowerShell” en el menú Inicio.
2. Ve al directorio del clon (ajusta la ruta):

   ```powershell
   cd C:\ruta\a\lexer-generator
   ```

3. Crea y activa el entorno virtual:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   Si aparece un error de **política de ejecución** (`running scripts is disabled`), ejecuta una vez en PowerShell **como administrador**:

   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

   Cierra y vuelve a abrir la terminal, luego repite el paso 3.

4. Instala el proyecto:

   ```powershell
   python -m pip install -U pip
   pip install -e ".[dev]"
   ```

#### Símbolo del sistema (CMD)

1. Abre **cmd** (`Win + R` → `cmd` → Intro).
2. Cambia al directorio del proyecto:

   ```cmd
   cd /d C:\ruta\a\lexer-generator
   ```

3. Entorno virtual e instalación:

   ```cmd
   py -3 -m venv .venv
   .venv\Scripts\activate.bat
   python -m pip install -U pip
   pip install -e ".[dev]"
   ```

#### Git Bash

Útil si ya usas [Git for Windows](https://git-scm.com/download/win). Las rutas siguen el estilo Unix (`/c/Users/...`).

1. Abre **Git Bash**.
2. Ve al repositorio y activa el entorno (Git Bash usa `Scripts/activate` sin extensión):

   ```bash
   cd /c/ruta/a/lexer-generator
   py -3 -m venv .venv
   source .venv/Scripts/activate
   python -m pip install -U pip
   pip install -e ".[dev]"
   ```

   Si `py` no existe, prueba `python` o `python3` según lo que tengas en PATH.

#### Windows: comprobar y herramientas opcionales

- Comprueba la CLI: `yalex --help`, `python -m yalex --help`, o sin venv: `python yalex_cli.py --help`.
- **Graphviz** (opcional, para PNG desde `.dot`): [instalador](https://graphviz.org/download/) o `winget install Graphviz.Graphviz`; comprueba que `dot` esté en el PATH.
- **Make** no viene con Windows. Para los mismos pasos que `make check`, usa la sección [Desarrollo](#desarrollo) a mano, o instala `make` con [Chocolatey](https://chocolatey.org/) (`choco install make`) o [Scoop](https://scoop.sh/).

---

### macOS

#### Terminal (instalador oficial de Python o python.org)

1. Abre **Terminal** (`Aplicaciones → Utilidades`).
2. En la carpeta del clon:

   ```bash
   cd ~/ruta/a/lexer-generator
   python3 -m venv .venv
   source .venv/bin/activate
   python -m pip install -U pip
   pip install -e ".[dev]"
   ```

#### Con Homebrew (opcional)

Si gestionas Python con [Homebrew](https://brew.sh/):

```bash
brew install python@3.12
# luego crea el venv con la ruta que muestre brew, p. ej.:
cd ~/ruta/a/lexer-generator
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

- **Graphviz** (opcional): `brew install graphviz`.
- **Make**: suele estar disponible tras instalar las herramientas de línea de comandos: `xcode-select --install`.

---

### Linux

Los pasos comunes son: paquetes del sistema (Python, `venv`, pip) → `cd` al clon → `python3 -m venv .venv` → `source .venv/bin/activate` → `pip install -e ".[dev]"`.

#### Debian / Ubuntu y derivados (Linux Mint, Pop!_OS, WSL2 Ubuntu, etc.)

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip graphviz build-essential git
cd ~/ruta/a/lexer-generator
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

#### Fedora / RHEL / CentOS Stream (con `dnf`)

```bash
sudo dnf install -y python3 python3-pip graphviz gcc git
cd ~/ruta/a/lexer-generator
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

#### Arch Linux

```bash
sudo pacman -S python python-pip graphviz base-devel git
cd ~/ruta/a/lexer-generator
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"
```

---

### Comprobar la instalación

Con el entorno virtual **activado** y estando en la raíz del repositorio:

```bash
pytest tests/ -q
python yalex_cli.py specs/yal/arithmetic_expression.yal -o _test_lexer --no-trees --no-dfa-graph -q
```

Opcional: `pre-commit install` (hooks de Ruff al hacer `git commit`; requiere `[dev]` instalado).

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
