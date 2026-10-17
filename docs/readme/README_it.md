# AXIOM

**Motore di ragionamento matematico**

*Un MCP per il calcolo, l'esplorazione e la verifica matematica.*

**Italiano** · [English](../../README.md) · [简体中文](README_zh.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Ελληνικά](README_el.md)

AXIOM è un'infrastruttura di matematica computazionale per agenti IA, ricercatori, studenti e sviluppatori. Collega qualsiasi client MCP a motori matematici specializzati — SymPy, SciPy, SageMath, Lean 4 — tramite un contratto unificato, con risultati tracciabili e **verificati in modo indipendente**.

Non è una calcolatrice potenziata dall'IA. Non è un altro Mathematica, SageMath o Lean. È l'infrastruttura che consente agli agenti di usarli tutti attraverso un'unica interfaccia.

> Ispirato alla filosofia di [REA](https://github.com/morluto/rea): *fare reverse engineering di qualsiasi cosa* → **analizzare la matematica**.

## Perché AXIOM

Un agente può affermare di aver risolto un'equazione. AXIOM **richiede una verifica indipendente** prima che un risultato sia considerato attendibile.

```
math solve "x^2 - 5*x + 6 = 0"
```

```text
┌─────────────────────────────────────────────────┐
│ Equazione di secondo grado                      │
│   x² - 5x + 6 = 0                               │
│                                                 │
│ Soluzioni                                       │
│   x = 2  oppure  x = 3                          │
│                                                 │
│ Motore        SymPy                             │
│ Verifica      Sostituzione esatta (frazioni)    │
│ Garanzia      VERIFIED-SUBSTITUTION             │
│ Risultato     Entrambe le radici sono soluzioni │
└─────────────────────────────────────────────────┘
```

### Livelli di garanzia

Non tutti i risultati matematici hanno la stessa forza logica. AXIOM distingue esplicitamente ogni livello:

| Livello | Significato |
| --- | --- |
| `exact-symbolic` | Identità simbolica verificata (ad es. semplificazione canonica) |
| `verified-substitution` | Soluzione convalidata per sostituzione con aritmetica esatta |
| `numerical-approximation` | Approssimazione numerica con un errore dichiarato |
| `formal-proof` | Dimostrazione verificata da un kernel di dimostrazione (Lean 4) |
| `heuristic` | Risultato probabile, non del tutto verificato |
| `unverified` | Calcolo grezzo, non ancora verificato |

Ogni risultato porta metadati di evidenza: `engine`, `engine_version`, `steps`, `limitations` e `reproducible_with`.

## Filosofia (ereditata da REA)

| REA | AXIOM |
| --- | --- |
| Fare reverse engineering di qualsiasi cosa | Analizzare la matematica |
| Analisi binaria | Analisi di espressioni e strutture |
| Ghidra / Hopper / IDA | SymPy / SageMath / Julia / Lean 4 |
| Tracciamento del codice | Tracciamento delle soluzioni |
| Evidenze di reverse engineering | Evidenze matematiche |
| Decompilazione | Semplificazione e scomposizione algebrica |
| Ispezione delle funzioni | Analisi delle funzioni |
| Confronto dei comportamenti | Verifica di equivalenza |
| MCP per agenti | MCP per agenti matematici |
| CLI | CLI matematica |

## Architettura

```text
┌──────────────────────────────────────────────────────────┐
│  Agenti IA                                               │
│  Codex · Claude Code · Gemini CLI · altri client MCP     │
└────────────────────────┬─────────────────────────────────┘
                         │  MCP / CLI
┌────────────────────────▼─────────────────────────────────┐
│  Nucleo di AXIOM                                         │
│  Parser · Dispatcher · Registro dei motori · Evidenze ·  │
│  Verifica                                                │
└──┬──────────┬──────────┬──────────┬───────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
 Simbolico  Numerico    Formale    Visualizzazione
 SymPy      SciPy       Lean 4     Plotly · Manim
 SageMath   Julia       Mathlib
```

Lo stesso contratto vale indipendentemente dal software che esegue il calcolo: cambiare motore non modifica né il formato del risultato né il livello di garanzia.

## Moduli

| Modulo | Capacità |
| --- | --- |
| `arithmetic` | Aritmetica esatta, frazioni, precisione arbitraria |
| `algebra` | Equazioni, polinomi, fattorizzazione, semplificazione |
| `calculus` | Limiti, derivate, integrali, serie |
| `linear-algebra` | Matrici, autovalori, decomposizioni |
| `geometry` | Geometria euclidea, analitica e differenziale |
| `number-theory` | Numeri primi, congruenze, equazioni diofantee |
| `discrete` | Combinatoria, grafi, logica |
| `statistics` | Probabilità, distribuzioni, inferenza |
| `optimization` | Ottimizzazione lineare, non lineare e convessa |
| `differential-equations` | ODE, PDE e sistemi dinamici |
| `numerical` | Metodi numerici, approssimazioni ed errori |
| `symbolic` | Manipolazione simbolica generale |
| `proof` | Dimostrazioni, controesempi e verifica formale |
| `visualization` | Grafici 2D/3D, animazioni e campi vettoriali |
| `research` | Esplorazione di congetture, ipotesi ed esperimenti |

## Strumenti MCP

Strumenti piccoli e componibili:

```
math_parse        math_simplify     math_solve
math_differentiate   math_integrate  math_limit
math_evaluate      math_plot         math_prove
math_verify        math_explain      math_compare
math_explore
```

CLI proposta:

```bash
math solve "x^2 - 5*x + 6 = 0"
math integrate "sin(x)^2" --variable x
math plot "sin(x)/x" --range -10:10
math prove theorem.lean --engine lean
math verify solution.json
```

## Roadmap

- [ ] **v0.1 — Fondamenta**: CLI, MCP, parser di espressioni, SymPy, risoluzione di equazioni ed evidenze.
- [ ] **v0.2 — Numerico**: SciPy, matrici, integrazione numerica, ottimizzazione e valutazione degli errori.
- [ ] **v0.3 — Verifica**: verificatori indipendenti e integrazione opzionale di Lean 4.
- [ ] **v0.4 — Visualizzazione**: grafici interattivi, geometria e visualizzazione di sistemi dinamici.
- [ ] **v1.0 — Ricerca**: composizione automatica di strumenti, esperimenti riproducibili ed esplorazione assistita di congetture.

Iniziamo con tre motori: **SymPy** (simbolico), **SciPy** (numerico) e **Lean 4** (dimostrazioni formali).

## Struttura del repository

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

## Nome

**AXIOM** — *Motore di ragionamento matematico*. Un'identità propria, allineata alla matematica formale e alla ricerca.

## Licenza

MIT

## Relazione con MathTools Offline

Questo repository era *MathTools Offline* (una suite desktop offline per LaTeX/SymPy/Lean). È stato rinominato **AXIOM** e riposizionato come infrastruttura di matematica computazionale per gli agenti. I motori (SymPy, Lean 4) sono condivisi a livello concettuale, ma ora l'attenzione è rivolta al contratto MCP unificato e alla verifica indipendente dei risultati.
