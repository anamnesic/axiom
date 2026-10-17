# AXIOM

**Engine für mathematisches Schließen**

*Ein MCP für mathematische Berechnung, Exploration und Verifikation.*

**Deutsch** · [English](../../README.md) · [简体中文](README_zh.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Español](README_es.md) · [Français](README_fr.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md)

AXIOM ist eine Infrastruktur für computergestützte Mathematik für KI-Agenten, Forschende, Studierende und Entwickler. Sie verbindet jeden MCP-Client über einen einheitlichen Vertrag mit spezialisierten Mathematik-Engines — SymPy, SciPy, SageMath, Lean 4 — und liefert nachvollziehbare Ergebnisse, die **unabhängig verifiziert** werden.

Es ist kein KI-gestützter Taschenrechner. Es ist kein weiteres Mathematica, SageMath oder Lean. Es ist die Infrastruktur, mit der Agenten all diese Systeme über eine einzige Schnittstelle nutzen können.

> Inspiriert von der Philosophie von [REA](https://github.com/morluto/rea): *alles rückentwickeln* → **Mathematik analysieren**.

## Warum AXIOM

Ein Agent mag behaupten, eine Gleichung gelöst zu haben. AXIOM **verlangt eine unabhängige Verifikation**, bevor ein Ergebnis als vertrauenswürdig gilt.

```
math solve "x^2 - 5*x + 6 = 0"
```

```text
┌─────────────────────────────────────────────────┐
│ Quadratische Gleichung                          │
│   x² - 5x + 6 = 0                               │
│                                                 │
│ Lösungen                                        │
│   x = 2  oder  x = 3                            │
│                                                 │
│ Engine        SymPy                             │
│ Verifikation  Exakte Einsetzung (Brüche)        │
│ Garantie      VERIFIED-SUBSTITUTION             │
│ Ergebnis      Beide Wurzeln sind Lösungen       │
└─────────────────────────────────────────────────┘
```

### Garantie-Stufen

Nicht jedes mathematische Ergebnis hat dieselbe logische Aussagekraft. AXIOM unterscheidet die einzelnen Stufen ausdrücklich:

| Stufe | Bedeutung |
| --- | --- |
| `exact-symbolic` | Verifizierte symbolische Identität (z. B. kanonische Vereinfachung) |
| `verified-substitution` | Durch Einsetzung mit exakter Arithmetik validierte Lösung |
| `numerical-approximation` | Numerische Näherung mit angegebenem Fehler |
| `formal-proof` | Von einem Beweiskern verifizierter Beweis (Lean 4) |
| `heuristic` | Wahrscheinliches, aber nicht vollständig verifiziertes Ergebnis |
| `unverified` | Rohberechnung, noch nicht verifiziert |

Jedes Ergebnis trägt Nachweis-Metadaten: `engine`, `engine_version`, `steps`, `limitations` und `reproducible_with`.

## Philosophie (von REA übernommen)

| REA | AXIOM |
| --- | --- |
| Alles rückentwickeln | Mathematik analysieren |
| Binäranalyse | Analyse von Ausdrücken und Strukturen |
| Ghidra / Hopper / IDA | SymPy / SageMath / Julia / Lean 4 |
| Code-Tracing | Lösungs-Tracing |
| Reverse-Engineering-Nachweise | Mathematische Nachweise |
| Dekompilierung | Vereinfachung und algebraische Zerlegung |
| Funktionsinspektion | Funktionsanalyse |
| Verhaltensvergleich | Äquivalenzverifikation |
| MCP für Agenten | MCP für mathematische Agenten |
| CLI | Mathematisches CLI |

## Architektur

```text
┌──────────────────────────────────────────────────────────┐
│  KI-Agenten                                              │
│  Codex · Claude Code · Gemini CLI · weitere MCP-Clients  │
└────────────────────────┬─────────────────────────────────┘
                         │  MCP / CLI
┌────────────────────────▼─────────────────────────────────┐
│  AXIOM Core                                              │
│  Parser · Dispatcher · Engine-Registry · Nachweise ·     │
│  Verifikation                                            │
└──┬──────────┬──────────┬──────────┬───────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
 Symbolisch Numerisch   Formal     Visualisierung
 SymPy      SciPy       Lean 4     Plotly · Manim
 SageMath   Julia       Mathlib
```

Derselbe Vertrag gilt unabhängig davon, welche Software die Berechnung ausführt: Ein Wechsel der Engines ändert weder das Ergebnisformat noch die Garantie-Stufe.

## Module

| Modul | Fähigkeiten |
| --- | --- |
| `arithmetic` | Exakte Arithmetik, Brüche, beliebige Genauigkeit |
| `algebra` | Gleichungen, Polynome, Faktorisierung, Vereinfachung |
| `calculus` | Grenzwerte, Ableitungen, Integrale, Reihen |
| `linear-algebra` | Matrizen, Eigenwerte, Zerlegungen |
| `geometry` | Euklidische, analytische und Differentialgeometrie |
| `number-theory` | Primzahlen, Kongruenzen, diophantische Gleichungen |
| `discrete` | Kombinatorik, Graphen, Logik |
| `statistics` | Wahrscheinlichkeit, Verteilungen, Inferenz |
| `optimization` | Lineare, nichtlineare und konvexe Optimierung |
| `differential-equations` | ODEs, PDEs und dynamische Systeme |
| `numerical` | Numerische Verfahren, Approximationen und Fehler |
| `symbolic` | Allgemeine symbolische Manipulation |
| `proof` | Beweise, Gegenbeispiele und formale Verifikation |
| `visualization` | 2D/3D-Plots, Animationen und Vektorfelder |
| `research` | Vermutungsexploration, Hypothesen und Experimente |

## MCP-Werkzeuge

Kleine, kombinierbare Werkzeuge:

```
math_parse        math_simplify     math_solve
math_differentiate   math_integrate  math_limit
math_evaluate      math_plot         math_prove
math_verify        math_explain      math_compare
math_explore
```

Vorgeschlagenes CLI:

```bash
math solve "x^2 - 5*x + 6 = 0"
math integrate "sin(x)^2" --variable x
math plot "sin(x)/x" --range -10:10
math prove theorem.lean --engine lean
math verify solution.json
```

## Roadmap

- [ ] **v0.1 — Grundlagen**: CLI, MCP, Ausdrucksparser, SymPy, Gleichungslösen und Nachweise.
- [ ] **v0.2 — Numerik**: SciPy, Matrizen, numerische Integration, Optimierung und Fehlerbewertung.
- [ ] **v0.3 — Verifikation**: unabhängige Verifizierer und optionale Integration von Lean 4.
- [ ] **v0.4 — Visualisierung**: interaktive Plots, Geometrie und Visualisierung dynamischer Systeme.
- [ ] **v1.0 — Forschung**: automatisierte Werkzeugkomposition, reproduzierbare Experimente und unterstützte Vermutungsexploration.

Wir beginnen mit drei Engines: **SymPy** (symbolisch), **SciPy** (numerisch) und **Lean 4** (formale Beweise).

## Repository-Struktur

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

## Name

**AXIOM** — *Engine für mathematisches Schließen*. Eine eigenständige Identität, ausgerichtet auf formale Mathematik und Forschung.

## Lizenz

MIT

## Verhältnis zu MathTools Offline

Dieses Repository war *MathTools Offline* (eine Offline-Desktop-Suite für LaTeX/SymPy/Lean). Es wurde in **AXIOM** umbenannt und als Infrastruktur für computergestützte Mathematik für Agenten neu positioniert. Die Engines (SymPy, Lean 4) werden konzeptionell geteilt, doch der Fokus liegt nun auf dem einheitlichen MCP-Vertrag und der unabhängigen Verifikation von Ergebnissen.
