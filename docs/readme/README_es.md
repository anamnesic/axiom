# AXIOM

**Motor de razonamiento matemático**

*Un MCP para el cálculo, la exploración y la verificación matemáticos.*

**Español** · [English](../../README.md) · [简体中文](README_zh.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Français](README_fr.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md)

AXIOM es una infraestructura de matemática computacional para agentes de IA, investigadores, estudiantes y desarrolladores. Conecta cualquier cliente MCP con motores matemáticos especializados — SymPy, SciPy, SageMath, Lean 4 — mediante un contrato unificado, con resultados trazables que se **verifican de forma independiente**.

No es una calculadora con IA. No es otro Mathematica, SageMath o Lean. Es la infraestructura que permite a los agentes usar todos ellos a través de una única interfaz.

> Inspirado en la filosofía de [REA](https://github.com/morluto/rea): *ingeniería inversa de cualquier cosa* → **analizar las matemáticas**.

## Por qué AXIOM

Un agente puede afirmar que ha resuelto una ecuación. AXIOM **exige una verificación independiente** antes de dar un resultado por válido.

```
math solve "x^2 - 5*x + 6 = 0"
```

```text
┌─────────────────────────────────────────────────┐
│ Ecuación cuadrática                             │
│   x² - 5x + 6 = 0                               │
│                                                 │
│ Soluciones                                      │
│   x = 2  o  x = 3                               │
│                                                 │
│ Motor         SymPy                             │
│ Verificación  Sustitución exacta (fracciones)   │
│ Garantía      VERIFIED-SUBSTITUTION             │
│ Resultado     Ambas raíces son soluciones       │
└─────────────────────────────────────────────────┘
```

### Niveles de garantía

No todos los resultados matemáticos tienen la misma fuerza lógica. AXIOM distingue explícitamente cada nivel:

| Nivel | Significado |
| --- | --- |
| `exact-symbolic` | Identidad simbólica verificada (p. ej., simplificación canónica) |
| `verified-substitution` | Solución validada por sustitución con aritmética exacta |
| `numerical-approximation` | Aproximación numérica con un error declarado |
| `formal-proof` | Demostración verificada por un núcleo de prueba (Lean 4) |
| `heuristic` | Resultado probable, no verificado por completo |
| `unverified` | Cálculo en bruto, aún sin verificar |

Todos los resultados incluyen metadatos de evidencia: `engine`, `engine_version`, `steps`, `limitations` y `reproducible_with`.

## Filosofía (heredada de REA)

| REA | AXIOM |
| --- | --- |
| Ingeniería inversa de cualquier cosa | Analizar las matemáticas |
| Análisis binario | Análisis de expresiones y estructuras |
| Ghidra / Hopper / IDA | SymPy / SageMath / Julia / Lean 4 |
| Trazado de código | Trazado de soluciones |
| Evidencia de ingeniería inversa | Evidencia matemática |
| Descompilación | Simplificación y descomposición algebraica |
| Inspección de funciones | Análisis de funciones |
| Comparación de comportamiento | Verificación de equivalencia |
| MCP para agentes | MCP para agentes matemáticos |
| CLI | CLI matemática |

## Arquitectura

```text
┌──────────────────────────────────────────────────────────┐
│  Agentes de IA                                           │
│  Codex · Claude Code · Gemini CLI · otros clientes MCP   │
└────────────────────────┬─────────────────────────────────┘
                         │  MCP / CLI
┌────────────────────────▼─────────────────────────────────┐
│  Núcleo de AXIOM                                         │
│  Parser · Dispatcher · Registro de motores · Evidencia · │
│  Verificación                                            │
└──┬──────────┬──────────┬──────────┬───────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
 Simbólico  Numérico    Formal     Visualización
 SymPy      SciPy       Lean 4     Plotly · Manim
 SageMath   Julia       Mathlib
```

El mismo contrato se mantiene independientemente de qué software realice el cálculo: cambiar de motor no altera ni el formato del resultado ni el nivel de garantía.

## Módulos

| Módulo | Capacidades |
| --- | --- |
| `arithmetic` | Aritmética exacta, fracciones, precisión arbitraria |
| `algebra` | Ecuaciones, polinomios, factorización, simplificación |
| `calculus` | Límites, derivadas, integrales, series |
| `linear-algebra` | Matrices, valores propios, descomposiciones |
| `geometry` | Geometría euclidiana, analítica y diferencial |
| `number-theory` | Números primos, congruencias, ecuaciones diofánticas |
| `discrete` | Combinatoria, grafos, lógica |
| `statistics` | Probabilidad, distribuciones, inferencia |
| `optimization` | Optimización lineal, no lineal y convexa |
| `differential-equations` | EDO, EDP y sistemas dinámicos |
| `numerical` | Métodos numéricos, aproximaciones y errores |
| `symbolic` | Manipulación simbólica general |
| `proof` | Demostraciones, contraejemplos y verificación formal |
| `visualization` | Gráficos 2D/3D, animaciones y campos vectoriales |
| `research` | Exploración de conjeturas, hipótesis y experimentos |

## Herramientas MCP

Herramientas pequeñas y componibles:

```
math_parse        math_simplify     math_solve
math_differentiate   math_integrate  math_limit
math_evaluate      math_plot         math_prove
math_verify        math_explain      math_compare
math_explore
```

CLI propuesta:

```bash
math solve "x^2 - 5*x + 6 = 0"
math integrate "sin(x)^2" --variable x
math plot "sin(x)/x" --range -10:10
math prove theorem.lean --engine lean
math verify solution.json
```

## Hoja de ruta

- [ ] **v0.1 — Fundamentos**: CLI, MCP, analizador de expresiones, SymPy, resolución de ecuaciones y evidencia.
- [ ] **v0.2 — Numérico**: SciPy, matrices, integración numérica, optimización y evaluación de errores.
- [ ] **v0.3 — Verificación**: verificadores independientes e integración opcional con Lean 4.
- [ ] **v0.4 — Visualización**: gráficos interactivos, geometría y visualización de sistemas dinámicos.
- [ ] **v1.0 — Investigación**: composición automatizada de herramientas, experimentos reproducibles y exploración asistida de conjeturas.

Empezamos con tres motores: **SymPy** (simbólico), **SciPy** (numérico) y **Lean 4** (demostraciones formales).

## Estructura del repositorio

```
axiom/
├── README.md
├── LICENSE
├── AGENTS.md
├── Cargo.toml
├── crates/
│   ├── core/
│   ├── cli/
│   ├── mcp/
│   ├── evidence/
│   ├── verification/
│   └── engine-registry/
├── engines/
│   ├── sympy/
│   ├── sagemath/
│   ├── scipy/
│   ├── julia/
│   └── lean/
├── domains/
│   ├── algebra/
│   ├── calculus/
│   ├── geometry/
│   ├── discrete/
│   ├── number-theory/
│   ├── dynamical-systems/
│   └── optimization/
├── skills/
│   └── mathematics/
├── examples/
├── benchmarks/
├── tests/
└── docs/
```

## Nombre

**AXIOM** — *Motor de razonamiento matemático*. Una identidad propia, alineada con las matemáticas formales y la investigación.

## Licencia

MIT

## Relación con MathTools Offline

Este repositorio era *MathTools Offline* (una suite de escritorio sin conexión para LaTeX/SymPy/Lean). Se renombró a **AXIOM** y se reposicionó como infraestructura de matemática computacional para agentes. Los motores (SymPy, Lean 4) se comparten conceptualmente, pero ahora el foco está en el contrato MCP unificado y en la verificación independiente de los resultados.
