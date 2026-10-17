# AXIOM

**Mathematical Reasoning Engine**

*One MCP for mathematical computation, exploration, and verification.*

AXIOM é uma infraestrutura de matemática computacional para agentes de IA, pesquisadores, estudantes e desenvolvedores. Ele conecta qualquer cliente MCP a engines matemáticas especializadas — SymPy, SciPy, SageMath, Lean 4 — através de um contrato unificado, com resultados rastreáveis e **verificados de forma independente**.

Não é uma calculadora com IA. Não é outro Mathematica, SageMath ou Lean. É a infraestrutura que permite aos agentes utilizar todos eles por uma interface única.

> Inspirado na filosofia do [REA](https://github.com/morluto/rea): *reverse engineer anything* → **analyze mathematics**.

## Por que AXIOM

Um agente pode dizer que resolveu uma equação. O AXIOM **exige verificação independente** antes de tratar o resultado como confiável.

```
math solve "x^2 - 5*x + 6 = 0"
```

```text
┌─────────────────────────────────────────────────┐
│ Equação quadrática                             │
│   x² - 5x + 6 = 0                              │
│                                                 │
│ Soluções                                        │
│   x = 2  ou  x = 3                              │
│                                                 │
│ Engine        SymPy                             │
│ Verificação   Substituição exata (frações)      │
│ Garantia      VERIFIED-SUBSTITUTION             │
│ Resultado     Ambas as raízes satisfazem a eq.  │
└─────────────────────────────────────────────────┘
```

### Níveis de garantia

Nem todo resultado matemático tem a mesma força lógica. O AXIOM distingue explicitamente cada nível:

| Nível | Significado |
| --- | --- |
| `exact-symbolic` | Identidade simbólica verificada (ex.: simplificação canônica) |
| `verified-substitution` | Solução validada por substituição com aritmética exata |
| `numerical-approximation` | Aproximação numérica com erro declarado |
| `formal-proof` | Demonstração verificada por um kernel de prova (Lean 4) |
| `heuristic` | Resultado provável, sem verificação completa |
| `unverified` | Cálculo bruto, ainda não verificado |

Todo resultado carrega metadados de evidência: `engine`, `engine_version`, `steps`, `limitations` e `reproducible_with`.

## Filosofia (herdada do REA)

| REA | AXIOM |
| --- | --- |
| Reverse engineer anything | Analyze mathematics |
| Análise de binários | Análise de expressões e estruturas |
| Ghidra / Hopper / IDA | SymPy / SageMath / Julia / Lean 4 |
| Rastreamento de código | Rastreamento de soluções |
| Evidências de engenharia reversa | Evidências matemáticas |
| Decompilação | Simplificação e decomposição algébrica |
| Inspeção de funções | Análise de funções |
| Comparação de comportamento | Verificação de equivalência |
| MCP para agentes | MCP para agentes matemáticos |
| CLI | CLI matemática |

## Arquitetura

```text
┌──────────────────────────────────────────────────────────┐
│  Agentes de IA                                           │
│  Codex · Claude Code · Gemini CLI · outros MCP clients   │
└────────────────────────┬─────────────────────────────────┘
                         │  MCP / CLI
┌────────────────────────▼─────────────────────────────────┐
│  Núcleo AXIOM                                            │
│  Parser · Dispatcher · Engine Registry · Evidence ·      │
│  Verification                                            │
└──┬──────────┬──────────┬──────────┬───────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
 Symbolic   Numerical   Formal     Visualization
 SymPy      SciPy       Lean 4     Plotly · Manim
 SageMath   Julia       Mathlib
```

O mesmo contrato vale independentemente do software responsável pelo cálculo: trocar de engine não muda o formato do resultado nem o nível de garantia.

## Módulos

| Módulo | Capacidades |
| --- | --- |
| `arithmetic` | Aritmética exata, frações, precisão arbitrária |
| `algebra` | Equações, polinômios, fatoração, simplificação |
| `calculus` | Limites, derivadas, integrais, séries |
| `linear-algebra` | Matrizes, autovalores, decomposições |
| `geometry` | Geometria euclidiana, analítica e diferencial |
| `number-theory` | Primos, congruências, equações diofantinas |
| `discrete` | Combinatória, grafos, lógica |
| `statistics` | Probabilidade, distribuições, inferência |
| `optimization` | Otimização linear, não linear e convexa |
| `differential-equations` | EDOs, EDPs e sistemas dinâmicos |
| `numerical` | Métodos numéricos, aproximações e erros |
| `symbolic` | Manipulação simbólica geral |
| `proof` | Demonstrações, contraexemplos e verificação formal |
| `visualization` | Gráficos 2D/3D, animações e campos vetoriais |
| `research` | Exploração de conjecturas, hipóteses e experimentos |

## Ferramentas MCP

Ferramentas pequenas, combináveis:

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

- [ ] **v0.1 — Foundation**: CLI, MCP, parser de expressões, SymPy, resolução de equações e evidências.
- [ ] **v0.2 — Numerical**: SciPy, matrizes, integração numérica, otimização e avaliação de erros.
- [ ] **v0.3 — Verification**: verificadores independentes e integração opcional com Lean 4.
- [ ] **v0.4 — Visualization**: gráficos interativos, geometria e visualização de sistemas dinâmicos.
- [ ] **v1.0 — Research**: composição automatizada de ferramentas, experimentos reprodutíveis e exploração assistida de conjecturas.

Começamos com três engines: **SymPy** (simbólico), **SciPy** (numérico) e **Lean 4** (provas formais).

## Estrutura do repositório

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

**AXIOM** — *Mathematical Reasoning Engine*. Identidade própria, alinhada à matemática formal e à pesquisa.

## Licença

MIT

## Relação com o MathTools Offline

Este repositório era o *MathTools Offline* (suíte desktop offline para LaTeX/SymPy/Lean). Foi renomeado para **AXIOM** e reposicionado como infraestrutura de matemática computacional para agentes. Os engines (SymPy, Lean 4) são compartilhados conceitualmente, mas o foco agora é o contrato MCP unificado e a verificação independente de resultados.
