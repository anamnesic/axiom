# AXIOM

**Moteur de raisonnement mathématique**

*Un MCP pour le calcul, l'exploration et la vérification mathématiques.*

**Français** · [English](../../README.md) · [简体中文](README_zh.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md)

AXIOM est une infrastructure de mathématiques computationnelles destinée aux agents d'IA, aux chercheurs, aux étudiants et aux développeurs. Elle connecte n'importe quel client MCP à des moteurs mathématiques spécialisés — SymPy, SciPy, SageMath, Lean 4 — via un contrat unifié, avec des résultats traçables et **vérifiés de manière indépendante**.

Ce n'est pas une calculatrice dopée à l'IA. Ce n'est pas un nouveau Mathematica, SageMath ou Lean. C'est l'infrastructure qui permet aux agents de les utiliser tous à travers une interface unique.

> Inspiré par la philosophie de [REA](https://github.com/morluto/rea) : *tout rétro-ingénierer* → **analyser les mathématiques**.

## Pourquoi AXIOM

Un agent peut prétendre avoir résolu une équation. AXIOM **exige une vérification indépendante** avant qu'un résultat soit considéré comme fiable.

```
math solve "x^2 - 5*x + 6 = 0"
```

```text
┌─────────────────────────────────────────────────┐
│ Équation du second degré                        │
│   x² - 5x + 6 = 0                               │
│                                                 │
│ Solutions                                       │
│   x = 2  ou  x = 3                              │
│                                                 │
│ Moteur        SymPy                             │
│ Vérification  Substitution exacte (fractions)   │
│ Garantie      VERIFIED-SUBSTITUTION             │
│ Résultat      Les deux racines sont solutions   │
└─────────────────────────────────────────────────┘
```

### Niveaux de garantie

Tous les résultats mathématiques n'ont pas la même force logique. AXIOM distingue explicitement chaque niveau :

| Niveau | Signification |
| --- | --- |
| `exact-symbolic` | Identité symbolique vérifiée (p. ex. simplification canonique) |
| `verified-substitution` | Solution validée par substitution avec arithmétique exacte |
| `numerical-approximation` | Approximation numérique avec une erreur déclarée |
| `formal-proof` | Preuve vérifiée par un noyau de preuve (Lean 4) |
| `heuristic` | Résultat probable, non entièrement vérifié |
| `unverified` | Calcul brut, pas encore vérifié |

Chaque résultat porte des métadonnées de preuve : `engine`, `engine_version`, `steps`, `limitations` et `reproducible_with`.

## Philosophie (héritée de REA)

| REA | AXIOM |
| --- | --- |
| Tout rétro-ingénierer | Analyser les mathématiques |
| Analyse binaire | Analyse d'expressions et de structures |
| Ghidra / Hopper / IDA | SymPy / SageMath / Julia / Lean 4 |
| Traçage de code | Traçage de solutions |
| Preuves de rétro-ingénierie | Preuves mathématiques |
| Décompilation | Simplification et décomposition algébrique |
| Inspection de fonctions | Analyse de fonctions |
| Comparaison de comportements | Vérification d'équivalence |
| MCP pour agents | MCP pour agents mathématiques |
| CLI | CLI mathématique |

## Architecture

```text
┌──────────────────────────────────────────────────────────┐
│  Agents d'IA                                             │
│  Codex · Claude Code · Gemini CLI · autres clients MCP   │
└────────────────────────┬─────────────────────────────────┘
                         │  MCP / CLI
┌────────────────────────▼─────────────────────────────────┐
│  Cœur d'AXIOM                                            │
│  Parseur · Dispatcher · Registre de moteurs · Preuves ·  │
│  Vérification                                            │
└──┬──────────┬──────────┬──────────┬───────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
 Symbolique Numérique   Formel     Visualisation
 SymPy      SciPy       Lean 4     Plotly · Manim
 SageMath   Julia       Mathlib
```

Le même contrat s'applique quel que soit le logiciel qui effectue le calcul : changer de moteur ne modifie ni le format du résultat ni le niveau de garantie.

## Modules

| Module | Capacités |
| --- | --- |
| `arithmetic` | Arithmétique exacte, fractions, précision arbitraire |
| `algebra` | Équations, polynômes, factorisation, simplification |
| `calculus` | Limites, dérivées, intégrales, séries |
| `linear-algebra` | Matrices, valeurs propres, décompositions |
| `geometry` | Géométrie euclidienne, analytique et différentielle |
| `number-theory` | Nombres premiers, congruences, équations diophantiennes |
| `discrete` | Combinatoire, graphes, logique |
| `statistics` | Probabilités, distributions, inférence |
| `optimization` | Optimisation linéaire, non linéaire et convexe |
| `differential-equations` | EDO, EDP et systèmes dynamiques |
| `numerical` | Méthodes numériques, approximations et erreurs |
| `symbolic` | Manipulation symbolique générale |
| `proof` | Preuves, contre-exemples et vérification formelle |
| `visualization` | Graphiques 2D/3D, animations et champs vectoriels |
| `research` | Exploration de conjectures, hypothèses et expériences |

## Outils MCP

Des outils petits et composables :

```
math_parse        math_simplify     math_solve
math_differentiate   math_integrate  math_limit
math_evaluate      math_plot         math_prove
math_verify        math_explain      math_compare
math_explore
```

CLI proposée :

```bash
math solve "x^2 - 5*x + 6 = 0"
math integrate "sin(x)^2" --variable x
math plot "sin(x)/x" --range -10:10
math prove theorem.lean --engine lean
math verify solution.json
```

## Feuille de route

- [ ] **v0.1 — Fondations** : CLI, MCP, analyseur d'expressions, SymPy, résolution d'équations et preuves.
- [ ] **v0.2 — Numérique** : SciPy, matrices, intégration numérique, optimisation et évaluation des erreurs.
- [ ] **v0.3 — Vérification** : vérificateurs indépendants et intégration optionnelle de Lean 4.
- [ ] **v0.4 — Visualisation** : graphiques interactifs, géométrie et visualisation de systèmes dynamiques.
- [ ] **v1.0 — Recherche** : composition automatisée d'outils, expériences reproductibles et exploration assistée de conjectures.

Nous commençons avec trois moteurs : **SymPy** (symbolique), **SciPy** (numérique) et **Lean 4** (preuves formelles).

## Arborescence du dépôt

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

## Nom

**AXIOM** — *Moteur de raisonnement mathématique*. Une identité propre, alignée sur les mathématiques formelles et la recherche.

## Licence

MIT

## Relation avec MathTools Offline

Ce dépôt était *MathTools Offline* (une suite de bureau hors ligne pour LaTeX/SymPy/Lean). Il a été renommé **AXIOM** et repositionné comme infrastructure de mathématiques computationnelles pour les agents. Les moteurs (SymPy, Lean 4) sont conceptuellement partagés, mais l'accent porte désormais sur le contrat MCP unifié et la vérification indépendante des résultats.
