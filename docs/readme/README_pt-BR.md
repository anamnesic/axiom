# AXIOM

**Motor de Raciocínio Matemático**

*Um único MCP para investigação, computação e verificação matemática.*

**[Research Math for All Time by Chronokairo](https://chronokairo.com)**

[English](../../README.md) · [简体中文](README_zh.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · **Português (Brasil)** · [العربية](README_ar.md) · [فarسی](README_fa.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md)

O AXIOM é uma infraestrutura de matemática computacional para agentes de IA, pesquisadores, estudantes e engenheiros de software. Ele conecta qualquer cliente Model Context Protocol (MCP) a motores matemáticos especializados — **SymPy**, **mpmath / SciPy**, **SageMath**, **Julia** e **Lean 4 / Mathlib 4** — através de um contrato unificado, onde cada resultado carrega evidências estruturadas e é **verificado de forma independente**.

Não é uma calculadora operada por IA. Não é outro Mathematica, SageMath ou Lean. É a infraestrutura neuro-simbólica que permite a agentes de raciocínio interagir com todos eles por meio de uma interface estritamente verificada.

> Inspirado na filosofia do [REA](https://github.com/morluto/rea): *reverse engineer anything* → **investigue matemática com agentes**.

---

## Por que AXIOM

Quando um agente de IA afirma que resolveu uma equação, ferramentas convencionais aceitam sua palavra. O AXIOM **exige verificação matemática independente** antes que a afirmação seja aceita como verdadeira.

```bash
axiom solve "x^2 - 5*x + 6 = 0"
```

```text
┌─ AXIOM · solve ───────────────────────────────────────────────────────────────────────┐
│ Solve            x^2 - 5*x + 6 = 0                                                    │
│ Result           ['2', '3']                                                           │
│ LaTeX            2, 3                                                                 │
│ Engine           sympy 1.14.0                                                         │
│ Method           algebraic solve (sympy.solve + domain & solveset completeness audit) │
│ Verification     exact-substitution: PASSED                                           │
│ Detail           Both roots satisfy the equation by exact substitution                │
│ Epistemic State  PROOF                                                                │
│ Guarantee        [VERIFIED] VERIFIED-SUBSTITUTION                                     │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Os Quatro Estados Epistêmicos

O AXIOM categoriza rigorosamente toda a produção computacional em **quatro estados epistêmicos mutuamente exclusivos** ([ADR-0017](../adr/0017-four-epistemic-states-and-soundness-governance.md)):

| Estado Epistêmico | Garantias Associadas | Definição Epistêmica | Critério Fail-Closed de Aceite |
| :--- | :--- | :--- | :--- |
| **Proof (Prova)** | `formal-proof`, `exact-symbolic`, `verified-substitution` | Verdade matemática certificada. Identidade simbólica exata, derivação checada pelo kernel Lean 4 (`#print axioms`), ou raízes verificadas por substituição exata. | `Verification.passed == True`, resíduo simbólico $0$, zero axiomas/hipóteses não declarados, alinhamento congruente. |
| **Approximation (Aproximação)** | `numerical-approximation` | Avaliação quantitativa ou sondagem de sequência limitada dentro de tolerância $\epsilon$. Absorção de float inexato é rejeitada. | Erro finito $\le \epsilon$, `equivalent == False`, `approximately_equal == True`. Nunca recebe `EXACT_SYMBOLIC`. |
| **Refutation (Refutação)** | `[REFUTED] DISPROVEN` | A proposição é decisivamente refutada por contraexemplo concreto ($f(x^*) \neq 0$), contradição ou resíduo não-nulo. | Verificação independente refuta a afirmação. `Verification.passed == False`, testemunha registrada em `detail`. |
| **Inconclusive (Inconclusão)** | `[UNVERIFIED] UNVERIFIED` | O valor de verdade não pode ser estabelecido dentro dos algoritmos simbólicos, limites de ramificação ou timeouts de execução. | Estado fail-closed seguro. `guarantee == Guarantee.UNVERIFIED`. Nunca promovido a prova. |

### Hierarquia de Garantias

Nem toda computação possui a mesma força lógica. O AXIOM separa **afirmações de correção matemática** (`is_mathematical_claim == True`, exigindo `Verification(passed=True)` executado) de **estados puramente operacionais** (`is_mathematical_claim == False`):

| Nível | Categoria | Significado |
| :--- | :--- | :--- |
| `formal-proof` | Afirmação Matemática | Prova verificada pelo kernel do Lean 4 (`#print axioms` auditado, sem `sorry`/`admit` e sem tautologias $X = X$) |
| `exact-symbolic` | Afirmação Matemática | Identidade simbólica verificada (simplificação canônica, derivação de antiderivada via TFC, L'Hôpital simbólico com `assumptions`) |
| `verified-substitution` | Afirmação Matemática | Solução validada por substituição independente ($f(r)=0$, $A A^{-1}=I$, $\nabla_\lambda g_{\mu\nu}=0$) com auditoria de polos e domínio |
| `numerical-approximation` | Afirmação Matemática | Avaliação com precisão arbitrária, teste de diferenças finitas, quadratura adaptativa ou limites bilaterais com `max_error` declarado |
| `structural-parse` | Estado Operacional | Parse seguro de AST validado por equivalência de re-parse canônico (`ast-roundtrip`) |
| `catalog-lookup` | Estado Operacional | Declaração indexada recuperada do catálogo do Mathlib 4 ou API Loogle |
| `sampled-visualization` | Estado Operacional | Coordenadas amostradas de curva 1D renderizadas em vetor SVG e prévia ASCII |
| `heuristic` | Estado Operacional | Padrão plausível, sumário exploratório ou conjectura aberta ainda não verificada |
| `unverified` | Estado Operacional | Alegação refutada, falha por polo interior / descontinuidade de salto, ou cálculo inconclusivo |

---

## Arquitetura

```text
┌──────────────────────────────────────────────────────────┐
│  Agentes de IA                                           │
│  Antigravity · Codex · Claude Code · Cursor · Copilot    │
└────────────────────────┬─────────────────────────────────┘
                         │  MCP (21 ferramentas) / CLI
┌────────────────────────▼─────────────────────────────────┐
│  Núcleo AXIOM                                            │
│  Safe AST Parser · Dispatcher · Engine Registry ·        │
│  Evidence · Independent Verification · Research Sessions │
└──┬──────────┬──────────┬──────────┬───────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
  Simbólico  Numérico   Formal     Visualização
  SymPy      mpmath     Lean 4     Vetor SVG Nativo
  SageMath   Julia      Mathlib4   Prévia ASCII · Matplotlib
```

---

## Início Rápido

```bash
# Clonar e instalar localmente
git clone https://github.com/chronokairo/axiom.git
cd axiom
pip install -e .

# Executar diagnóstico de ambiente e verificadores
axiom doctor

# Auto-configurar clientes de agentes (Antigravity, Claude Code, Cursor, Codex)
axiom setup --apply

# Iniciar servidor stdio MCP
axiom mcp
```

---

## 21 Ferramentas MCP Componíveis

| Categoria | Quantidade | Ferramentas |
| :--- | :---: | :--- |
| **1. Computação Matemática** | 12 | `math_simplify`, `math_solve`, `math_differentiate`, `math_integrate`, `math_limit`, `math_evaluate`, `math_matrix`, `math_ode`, `math_number_theory`, `math_optimize`, `math_statistics`, `math_tensor` |
| **2. Verificação e Prova Formal** | 3 | `math_prove`, `math_verify`, `math_compare` |
| **3. Diagnóstico e Estrutura** | 3 | `math_parse`, `math_explain`, `math_explore` |
| **4. Consulta a Catálogo** | 1 | `math_search_mathlib` |
| **5. Sessões e Visualização** | 2 | `math_plot`, `math_session` |

---

## Pesquisa Científica & Fundamentação Teórica

O AXIOM atua como infraestrutura para investigação científica rigorosa. Para justificativas teóricas, limites de decidibilidade e formalizações em Lean 4, consulte:

- **[Whitepaper de Pesquisa Científica (`RESEARCH.md`)](../../RESEARCH.md)**:
  - Taxonomia epistemológica e teoria da prova;
  - Limites de decidibilidade (Teorema de Richardson, Gödel, Teorema MRDP);
  - **Benchmark EXP-0001 ($n=21$ casos adversariais)**: 0.0% de taxa de falsos positivos, limite superior de 95% de confiança de $\approx 14.3\%$ via Regra dos Três vs 46.2% em CAS ingênuo (SymPy 1.12 sem envolucro);
  - **Sondas dos Problemas do Milênio ($n=111$ critérios, 40 controles negativos)**: Limite superior de 95% $\le 7.5\%$;
  - **Isenção de Sondas de Fronteira**: O AXIOM não afirma solucionar problemas abertos (Poincaré verificado como demonstrado por Perelman; Navier-Stokes valida decaimento clássico de Taylor-Green recusando alegações sem prova de blowup);
  - **Corpus Versionado de Aritmética (`research/arithmetic/`)**: Demonstrações formalizadas em Lean 4 do Teorema Fundamental da Aritmética (Hefez) auditadas no CI.
- **[Casos de Uso (`docs/use-cases.md`)](../use-cases.md)**: 10 fluxos de trabalho reais para agentes e pesquisadores.
- **[Catálogo de Skills (`docs/skills-catalog.md`)](../skills-catalog.md)**: 17 habilidades integradas para agentes.
- **[Histórico de Decisões Arquiteturais (`docs/adr/`)](../adr/README.md)**: 27 registros de decisões formais.

---

## Licença

Distribuído sob licença MIT. **[Research Math for All Time by Chronokairo](https://chronokairo.com)**
