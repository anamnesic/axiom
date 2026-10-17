# Panorama Competitivo — MCPs e Sistemas de Matemática Verificável para Agentes (2026)

> **Data da auditoria:** `2026-10-17` · **Versão do AXIOM auditada:** `v0.2.0`

Este documento mapeia o estado real do mercado de servidores MCP e sistemas de raciocínio matemático para agentes em 2026, com links diretos de evidência, versões inspecionadas e distinção rigorosa entre ferramentas de **cálculo verificado**, **prova formal**, **busca em catálogo**, **inspeção estrutural** e **visualização**.

---

## 1. Taxonomia Funcional das 21 Ferramentas do AXIOM (`v0.2.0`)

Para evitar sobrevenda epistemológica (como tratar parsing de AST ou busca de declarações como "prova simbólica"), o contrato [`Guarantee`](../src/axiom/contract.py) do AXIOM separa estritamente **reivindicações de correção matemática** (`Guarantee.is_mathematical_claim == True`) de **estados operacionais e estruturais** (`Guarantee.is_mathematical_claim == False`), imposto em tempo de execução por `MathResult.__post_init__`:

| Categoria Funcional | Qtd. | Ferramentas MCP | Nível de `Guarantee` em Caso de Sucesso | Mecanismo de Verificação (`Verification.kind`) |
| :--- | :---: | :--- | :--- | :--- |
| **1. Cálculo Matemático com Verificação Independente** | **12** | `math_simplify`, `math_solve`, `math_differentiate`, `math_integrate`, `math_limit`, `math_evaluate`, `math_matrix`, `math_ode`, `math_number_theory`, `math_optimize`, `math_statistics`, `math_tensor` | `exact-symbolic`, `verified-substitution` ou `numerical-approximation` | Redução simbólica + amostragem racional/transcendental, substituição exata + auditoria de polos, FTC + quadratura + detecção de singularidades interiores, limites laterais esquerdo/direito, Levi-Civita $\nabla_\lambda g_{\mu\nu}=0$, Bézout/CRT |
| **2. Verificação e Prova Formal** | **3** | `math_prove`, `math_verify`, `math_compare` | `formal-proof`, `exact-symbolic` ou `verified-substitution` | Kernel Lean 4 via `lake env lean` + auditoria `#print axioms` (`lean4-kernel-axiom-audit`), substituição independente ou busca de contraexemplos |
| **3. Inspeção Estrutural, Explicação e Exploração** | **3** | `math_parse`, `math_explain`, `math_explore` | `structural-parse` (`math_parse`) ou garantia herdada do cálculo | Round-trip determinístico da AST (`ast-roundtrip`) para `math_parse`; derivação auditada para `explain`/`explore` |
| **4. Busca em Catálogo Formal** | **1** | `math_search_mathlib` | `catalog-lookup` (ou `unverified` se 0 resultados) | Checagem de assinatura no catálogo Mathlib4 / Loogle (`catalog-signature-check` — **não** reivindica prova de identidade) |
| **5. Visualização e Sessão de Pesquisa** | **2** | `math_plot`, `math_session` | `sampled-visualization` (`math_plot`), elo mais fraco `chain_guarantee` (`math_session`) | Amostragem de domínio (`domain-sampling`) e auditoria de cadeia lógica (`chain-audit`) |

---

## 2. Concorrente Direto Principal: `symkit-mcp` (e `nsforge-mcp`)

O espaço de "CAS + verificação + Lean 4 + proveniência via MCP" **não está vazio**. O concorrente direto mais próximo e maduro do AXIOM é o **[LBurny/symkit-mcp](https://github.com/LBurny/symkit-mcp)** ([PyPI `symkit-mcp 1.13.0`](https://pypi.org/project/symkit-mcp/), licença Apache-2.0, inspecionado em `2026-10-17`), construído na linhagem iniciada pelo **[u9401066/nsforge-mcp](https://github.com/u9401066/nsforge-mcp)**.

### Radiografia técnica do `symkit-mcp`
- **Escopo e maturidade:** **47 ferramentas MCP** divididas em 10 categorias e **1.656 testes automatizados** (significativamente maior em volume de ferramentas e suíte de testes que o AXIOM `v0.2.0`, que possui **21 ferramentas MCP** e **37 métodos de teste `test_*`** em [`tests/test_axiom.py`](../tests/test_axiom.py)).
- **Foco central:** Derivações simbólicas passo a passo para física, engenharia, química e economia — combinando fórmulas conhecidas em novas fórmulas com histórico imutável e `session_rollback`.
- **Diferenciais onde o `symkit-mcp` supera o AXIOM hoje:**
  1. **Análise dimensional e semântica de símbolos (`register_symbol`, `check_symbol_conflicts`):** verifica unidades físicas e consistência dimensional em cada passo da derivação.
  2. **Biblioteca de fórmulas persistente com SQLite FTS5 (`formula_search`, `formula_get`, `formula_promote`):** índice local determinístico em 3 camadas (`seed`, `curated`, `staging`) com suporte multilíngue e fontes externas opcionais (`wikidata`, `scipy`, `biomodels`).
  3. **Instalador dedicado do ambiente Lean + Mathlib (`symkit-lean-setup`):** baixa `elan` + Lean 4 + cache pré-compilado do Mathlib (`~1–2 GB`).
- **O que o AXIOM `v0.2.0` incorporou e onde se diferencia:**
  1. **Hipóteses de domínio e detecção de contradições (`Parser(assumptions=...)`):** o AXIOM `v0.2.0` suporta hipóteses por variável (`positive`, `negative`, `real`, `integer`, `even`, `odd`, `nonzero`) com rejeição de hipóteses contraditórias (`positive` + `negative`, `even` + `odd`) e busca de contraexemplos racionais em *branch cuts* ($\sqrt{x^2} = x$ refutado em $x = -1$ sobre $\mathbb{R}$, mas verificado como `exact-symbolic` sob `assumptions={"x": "positive"}`).
  2. **Detecção de tautologias reflexivas triviais em Lean 4 (`detect_trivial_reflexive_theorems`):** inspirado no filtro de trivialidade do `symkit-mcp`, o [`LeanEngine`](../src/axiom/engines/lean_engine.py) sinaliza igualdades sintaticamente idênticas (`x = x`, `0 = 0`) em `trivial_theorems`.
  3. **Escopo da verificação Lean 4 e cálculo analítico:** enquanto o `session_certify` do `symkit-mcp` foca no fragmento racional de igualdades da sessão (`ring`/`field_simp`), o `math_prove` do AXIOM executa `lake env lean` + `#print axioms` sobre teoremas Lean 4 arbitrários, e os verificadores de cálculo do AXIOM detectam polos interiores não integráveis ($\int_{-1}^1 x^{-2}\,dx$) e descontinuidades de salto em limites bilaterais ($\lim_{x\to 0} |x|/x$).

### Comparação Direta: `symkit-mcp` vs `AXIOM`

| Dimensão | `LBurny/symkit-mcp` (`v1.13.0`, PyPI) | `chronokairo/axiom` (`v0.2.0`) |
| :--- | :--- | :--- |
| **Foco Primário** | Derivação passo a passo de fórmulas físicas/engenharia com análise dimensional | Raciocínio matemático multi-domínio com contrato tipado de garantias epistemológicas |
| **Volume de Ferramentas e Testes** | **47 tools MCP**, **1.656 testes** | **21 tools MCP** (12 cálculo, 3 prova/verificação, 3 estruturais, 1 catálogo, 2 plot/sessão), **37 métodos `test_*`** em `tests/test_axiom.py` + suíte formal Lean 4 |
| **Análise Dimensional (Unidades Físicas)** | **✅ Nativa (`register_symbol`, `check_symbol_conflicts`)** | ❌ Não possui |
| **Hipóteses sobre Símbolos & Conflitos** | **✅ (`assume`, `unassume`, `check_assumption_conflicts`)** | **✅ (`assumptions={"x": "positive"}` + detecção de pares contraditórios)** |
| **Biblioteca de Fórmulas Indexada (SQLite FTS5)** | **✅ Nativa (`seed` / `curated` / `staging`)** | ❌ Não possui (possui busca de teoremas Mathlib4 + Loogle classificada como `catalog-lookup`) |
| **Escopo da Certificação Lean 4** | Fragmento racional de igualdades algébricas da sessão (`ring` / `field_simp`) + filtro `trivial` | **Qualquer teorema/lema/exemplo Lean 4** (`math_prove`) via `lake env lean` + `#print axioms` + alerta `trivial_theorems` |
| **Taxonomia de Garantias no Contrato** | Status por passo (`verified` / `proven` / `trivial` / `unproven`) | **4 garantias matemáticas** (`formal-proof`, `exact-symbolic`, `verified-substitution`, `numerical-approximation`) + **4 estados operacionais** (`structural-parse`, `catalog-lookup`, `sampled-visualization`, `heuristic`) + `unverified` |
| **Auditoria de Singularidades, *Branch Cuts* e Limites Bilaterais** | Foco algébrico/dimensional | **✅ Detecção de polos interiores em integrais definidas, limites esquerdo vs. direito e raízes estranhas ($0/0$)** |
| **Geometria Diferencial / Tensores** | Vetores/transformadas gerais via tool `math` | **✅ Dedicada (`math_tensor`)** com verificação de compatibilidade métrica de Levi-Civita ($\nabla_\lambda g_{\mu\nu}=0$) |

---

## 3. Outros Servidores MCP de Matemática (Mapeamento Auditado em `2026-10-17`)

### A. Ecossistema Wolfram (Distinção entre as 3 Modalidades)
É essencial distinguir as **três ofertas diferentes** do ecossistema Wolfram, que possuem requisitos de licença, execução e autenticação distintos:

1. **Paclet Oficial Local [`WolframResearch/AgentTools`](https://github.com/WolframResearch/AgentTools) (Wolfram 15+ / Mathematica):**
   - **Como funciona:** Sobe um servidor MCP local conectado diretamente ao kernel Wolfram Language da máquina do usuário, com avaliação simbólica/numérica completa, sessão persistente e modo sandbox.
   - **Requisito:** Exige **instalação e licença local** do Wolfram Engine / Mathematica (Wolfram 15+).
2. **Endpoint Oficial Gratuito Wolfram Cloud MCP (Sem Chave de API):**
   - **Como funciona:** Serviço remoto gratuito da Wolfram que expõe consultas factuais e computacionais rápidas via Wolfram|Alpha para clientes MCP sem exigir cadastro de chave de API manual.
   - **Limitação:** Execução remota *stateless* na nuvem (não executa notebooks locais arbitrários nem funciona offline).
3. **[Wolfram MCP Service Comercial](https://www.wolfram.com/artificial-intelligence/mcp-service/) / Wolfram|Alpha LLM API & Wrappers de Terceiros ([`paraporoco/Wolfram-MCP`](https://github.com/paraporoco/Wolfram-MCP), [`ricocf/mcp-wolframalpha`](https://github.com/ricocf/mcp-wolframalpha), [`siqiliu-tsinghua/mma-mcp`](https://glama.ai/mcp/servers/siqiliu-tsinghua/mma-mcp/tree)):**
   - **Como funciona:** Serviços autenticados por `AppID` / chave de API comercial ou bridges comunitárias para instalações locais do Mathematica.
   - **Comparação com o AXIOM:** O motor do Mathematica é mais amplo em integração simbólica (Risch completo) e funções especiais, mas é proprietário/caixa-preta e não acopla verificação formal em Lean 4 nem contrato aberto de garantias.

### B. Ecossistema Lean 4 MCP
* **[oOo0oOo/lean-lsp-mcp](https://github.com/oOo0oOo/lean-lsp-mcp)** *(Oliver Dressler, citado em FLARE [`arXiv:2608.25220`](https://arxiv.org/abs/2608.25220))* & **[Numina-Lean-Agent](https://arxiv.org/pdf/2601.14027)** *(Project Numina)*
  * **Capacidades auditadas:** Conecta agentes ao servidor LSP do Lean 4 (`lean_goal`, `lean_diagnostic_messages`, `lean_loogle`, `lean_leansearch`) e **inclui a ferramenta `lean_verify`**, que inspeciona axiomas e bloqueia provas inseguras com `sorry`.
  * **Diferença para o AXIOM:** O `lean-lsp-mcp` é superior na **interação passo a passo com o LSP do Lean 4** (inspeção de *goal state* linha a linha), mas é dedicado exclusivamente à escrita de provas em Lean 4; não possui motores CAS (SymPy/Sage), cálculo numérico de alta precisão (`mpmath`), EDOs, tensores ou plotagem.
* **[sandraschi/leanforge-mcp](https://github.com/sandraschi/leanforge-mcp)**, **[lean-probe (`v0.3.1`)](https://pypi.org/project/lean-probe/0.3.1/)** e **[Lean-Prover/lean-prover](https://github.com/Lean-Prover/lean-prover)**: servidores MCP focados em compilação Lean 4 rápida, busca *best-of-N* e recuperação do Mathlib.

### C. Servidores CAS ("Calculadoras Simbólicas e Numéricas")
* **[Jsewill/math-mcp](https://github.com/Jsewill/math-mcp):** 36 ferramentas baseadas em SymPy com saída tipada e aritmética exata/precisão arbitrária.
* **[XBP-Europe/sagemath-mcp](https://github.com/XBP-Europe/sagemath-mcp):** ~40 ferramentas sobre o **SageMath** com sessão persistente.
* **[sdiehl/sympy-mcp](https://github.com/sdiehl/sympy-mcp):** wrapper SymPy (álgebra, cálculo, EDOs, matrizes e tensores via `einsteinpy`).
* **[abhiphile/fermat-mcp](https://github.com/abhiphile/fermat-mcp):** combina SymPy, NumPy e Matplotlib em um único servidor MCP.

---

## 4. Sistemas de Prova Formal com IA (Fora do Ecossistema MCP)

Estes sistemas atuam na fronteira de busca autônoma de provas formais:
* **Aristotle (Harmonic, [`arXiv:2510.01346`](https://arxiv.org/pdf/2510.01346v1)):** busca de provas em Lean 4 + solver geométrico (nível medalha de ouro na IMO 2025).
* **Gauss (Math Inc.):** agente de formalização em larga escala em Lean 4.
* **AlphaProof & AlphaProof Nexus (Google DeepMind):** RL + autoformalização em Lean 4.
* **DeepSeek-Prover-V2** & **Kimina-Prover** *(Project Numina)* e **Lean Copilot ([`arXiv:2404.12534`](https://www.arxiv.org/abs/2404.12534))**.

---

## 5. Matriz Comparativa Auditada (`2026-10-17`)

| Capacidade / Critério | `Jsewill/math-mcp` / `sdiehl/sympy-mcp` | `Wolfram` (`AgentTools` Local / Cloud MCP / API) | `oOo0oOo/lean-lsp-mcp` | `LBurny/symkit-mcp` (`v1.13.0`) | **AXIOM (`v0.2.0`)** |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Fonte / Evidência Auditada (`2026-10-17`)** | [GitHub `Jsewill/math-mcp`](https://github.com/Jsewill/math-mcp) · [GitHub `sdiehl/sympy-mcp`](https://github.com/sdiehl/sympy-mcp) | [GitHub `WolframResearch/AgentTools`](https://github.com/WolframResearch/AgentTools) · [Wolfram MCP Service](https://www.wolfram.com/artificial-intelligence/mcp-service/) | [GitHub `oOo0oOo/lean-lsp-mcp`](https://github.com/oOo0oOo/lean-lsp-mcp) | [GitHub `LBurny/symkit-mcp`](https://github.com/LBurny/symkit-mcp) · [PyPI `1.13.0`](https://pypi.org/project/symkit-mcp/) | [GitHub `chronokairo/axiom`](https://github.com/chronokairo/axiom) |
| **Licença & Execução** | Open Source (Local) | Proprietário: Local (`AgentTools`, requer Wolfram 15+), Cloud gratuito (sem API key) ou API paga | MIT (Local, requer projeto Lean 4) | Apache-2.0 (Local, 100% offline-first) | **MIT (Local, 100% offline-first)** |
| **Escopo & Testes** | 36 tools (`Jsewill`) / wrapper SymPy (`sdiehl`) | Ecossistema Wolfram Language completo | Focado em Lean 4 LSP | **47 tools MCP, 1.656 testes** | **21 tools MCP (5 categorias), 37 métodos `test_*` + job CI `formal-lean`** |
| **Álgebra, Cálculo, EDOs e Matrizes** | ✅ | ✅ | ❌ (Apenas Lean 4) | ✅ | ✅ |
| **Geometria Diferencial (Tensores), Teoria dos Números, Estatística e Otimização** | Tensores via `einsteinpy` (`sdiehl`); sem verificador independente | ✅ | ❌ | Vetores/transformadas via tool `math` | **✅ (Todos os 4 domínios com verificador independente próprio)** |
| **Análise Dimensional (Unidades) & Biblioteca SQLite FTS5 de Fórmulas** | ❌ | ✅ (`Quantity` / Wolfram Data) | ❌ | **✅ Nativa (`register_symbol`, `formula_search`)** | ❌ (Busca apenas catálogo Mathlib4/Loogle via `catalog-lookup`) |
| **Hipóteses de Domínio (`positive`, `integer`, etc.) & Conflitos** | Parcial (SymPy básico) | ✅ (`Assuming`) | ✅ (Tipos Lean 4) | **✅ (`assume`, `check_assumption_conflicts`)** | **✅ (`Parser(assumptions=...)` + detecção de contradições)** |
| **Inspeção Interativa de Metas Lean 4 via LSP (*Goal State*)** | ❌ | ❌ | **✅ Completa (`lean_goal`, LSP)** | ❌ | ❌ (Execução em lote via `lake env lean`) |
| **Prova Formal Lean 4 + Bloqueio de `sorry` / Auditoria de Axiomas** | ❌ | ❌ | **✅ (`lean_verify`)** | Igualdades racionais (`ring`/`field_simp`) + filtro `trivial` | **✅ (`#print axioms` + cobertura obrigatória + `trivial_theorems`)** |
| **Verificação Independente nas Operações de Cálculo** | ❌ (Retorna saída direta do SymPy) | ❌ (Avaliador único) | N/A (Não é CAS) | Explícita na sessão (`session_verify_step`, `session_verify_session`) | **✅ Automática nas 12 tools de cálculo e 3 de verificação** |
| **Separação Contratual: Prova/Cálculo vs Parse/Catálogo/Plot** | ❌ | ❌ | N/A | Status de passo (`verified`/`proven`/`trivial`/`unproven`) | **✅ (`is_mathematical_claim` separa provas de `structural-parse`, `catalog-lookup` e `sampled-visualization`)** |
| **Rastreamento do Elo Mais Fraco (`chain_guarantee`)** | ❌ | ❌ | ❌ | Histórico com `session_rollback` e `session_certify` | **✅ (`math_session` calcula `chain_guarantee` pelo elo mais fraco)** |
