# Panorama Competitivo — MCPs e Sistemas de Matemática Verificável para Agentes (2026)

Este documento mapeia o estado real do mercado de servidores MCP e sistemas de raciocínio matemático para agentes em 2026, incluindo concorrentes diretos neurossimbólicos (**`symkit-mcp`**, **`nsforge-mcp`**), o **MCP oficial da Wolfram**, o ecossistema **Lean 4 MCP** (**`lean-lsp-mcp`**, **`leanforge-mcp`**, **`lean-probe`**, **`lean-prover`**), wrappers CAS e os sistemas autônomos de prova formal fora do protocolo MCP (**Aristotle**, **Gauss**, **AlphaProof**, **Lean Copilot**).

---

## 1. Concorrente Direto Principal: `symkit-mcp` (e `nsforge-mcp`)

O espaço de "CAS + verificação + Lean 4 + proveniência via MCP" **não está vazio**. O concorrente direto mais próximo e maduro do AXIOM é o **[LBurny/symkit-mcp](https://github.com/LBurny/symkit-mcp)** (`v1.8.0`–`v1.13.0` no PyPI, licença Apache-2.0), construído na linhagem iniciada pelo **[u9401066/nsforge-mcp](https://github.com/u9401066/nsforge-mcp)**.

### Radiografia técnica do `symkit-mcp` (inspeção direta do repositório/PyPI)
- **Escopo e maturidade:** **47 ferramentas MCP** divididas em 10 categorias e **1.656 testes automatizados** (significativamente maior em volume de ferramentas e suíte de testes que o AXIOM `v0.1.x`).
- **Foco central:** Derivações simbólicas passo a passo para física, engenharia, química e economia — combinando fórmulas conhecidas em novas fórmulas com histórico imutável e `session_rollback`.
- **Diferenciais onde o `symkit-mcp` supera o AXIOM hoje:**
  1. **Análise dimensional e semântica de símbolos (`register_symbol`, `check_symbol_conflicts`):** verifica unidades físicas e consistência dimensional em cada passo da derivação.
  2. **Sistema explícito de hipóteses (`assume`, `unassume`, `check_assumption_conflicts`):** gerencia premissas sobre variáveis (ex.: `x nonzero`, `k > 0`) e detecta contradições entre hipóteses.
  3. **Biblioteca de fórmulas persistente com SQLite FTS5 (`formula_search`, `formula_get`, `formula_promote`):** índice local determinístico em 3 camadas (`seed`, `curated`, `staging`) com suporte multilíngue e fontes externas opcionais (`wikidata`, `scipy`, `biomodels`).
  4. **Filtro de trivialidade na certificação Lean (`session_certify`):** passos onde entrada e saída são idênticas (`x = x`, `0 = 0`) são classificados como `trivial` e excluídos da contagem `proven`.
  5. **Instalador dedicado do ambiente Lean + Mathlib (`symkit-lean-setup`):** baixa `elan` + Lean 4 + cache pré-compilado do Mathlib (`~1–2 GB`).

### Comparação Direta: `symkit-mcp` vs `AXIOM`

| Dimensão | `LBurny/symkit-mcp` (`v1.13.0`) | `chronokairo/axiom` (`v0.1.x`) |
| :--- | :--- | :--- |
| **Foco Primário** | Derivação passo a passo de fórmulas físicas/engenharia com análise dimensional | Raciocínio matemático multi-domínio com hierarquia explícita de garantias epistemológicas |
| **Maturidade / Suíte de Testes** | **Alta** (47 tools, **1.656 testes**, DDD maduro) | **Inicial (`v0.1.x`)** (21 tools, 30 suítes de teste + CI multiplataforma + Lean 4 live) |
| **Análise Dimensional (Unidades) & Conflito de Hipóteses** | **✅ Nativa (`register_symbol`, `check_assumption_conflicts`)** | ❌ Não possui |
| **Biblioteca de Fórmulas Indexada (SQLite FTS5)** | **✅ Nativa (`seed` / `curated` / `staging`)** | ❌ Não possui (possui catálogo Mathlib4 + Loogle) |
| **Escopo da Certificação Lean 4** | Focada no **fragmento racional de igualdades algébricas** da sessão (`simplify`/`expand`/`factor`/`combine` via `ring` / `field_simp`) | **Qualquer teorema/lema/exemplo Lean 4** (`math_prove`), auditado via `lake env lean` + `#print axioms` (com cobertura obrigatória de declarações) |
| **Hierarquia Tipada de Garantias em Todas as Respostas** | Binária/Status por passo (`verified` / `proven` / `trivial` / `unproven`) | **6 níveis ordenados (`Guarantee`)**: `formal-proof` > `exact-symbolic` > `verified-substitution` > `numerical-approximation` > `heuristic` > `unverified` |
| **Separação Estrita entre Simbólico Exato e Evidência Numérica** | Foco simbólico/dimensional | **✅ Explícita nos verificadores de cálculo** (ex.: integral confirmada apenas por quadratura recebe `numerical-approximation`; com FTC simbólico recebe `exact-symbolic`) |
| **Verificação Independente Automática por Domínio** | Via ferramentas de sessão (`session_verify_step`, `session_verify_session`) | **Automática em cada chamada**: FTC round-trip em derivadas/integrais, L'Hôpital/séries em limites, Levi-Civita $\nabla_\lambda g_{\mu\nu}=0$ em tensores, Bézout/CRT em teoria dos números |
| **Geometria Diferencial / Tensores (Métricas, Christoffel, Ricci)** | Vetores e transformadas via tool `math` | **✅ Dedicada (`math_tensor`)** com verificação de compatibilidade métrica de Levi-Civita e ausência de torção |
| **Plotagem Zero-Dependência (SVG/ASCII nativo)** | Exportação de scripts (`generate_output`) | **✅ (`math_plot`)** gera SVG vetorial e preview ASCII sem depender de Matplotlib |

---

## 2. Outros Servidores MCP de Matemática (Mapeamento Atualizado)

### A. Ecossistema Oficial e Comunitário Wolfram
* **[Wolfram MCP Service (Oficial)](https://www.wolfram.com/artificial-intelligence/mcp-service/)** & **Wolfram 15 `AgentTools` Paclet** (além de bridges como **[siqiliu-tsinghua/mma-mcp](https://glama.ai/mcp/servers/siqiliu-tsinghua/mma-mcp/tree)**, `paraporoco/Wolfram-MCP` e `ricocf/mcp-wolframalpha`)
  * **Atualização importante:** A Wolfram **não depende mais apenas de wrappers de terceiros**. O **Wolfram 15** inclui oficialmente o paclet `AgentTools`, que sobe um servidor MCP local com avaliador Wolfram Language, sessão persistente e modo sandbox, além do serviço MCP remoto oficial da Wolfram (que consulta o Wolfram|Alpha sem exigir chave de API manual para respostas factuais).
  * **Pontos fortes:** O motor simbólico e numérico do Mathematica (integração de Risch completa, funções especiais, dados curados) é o mais poderoso da indústria.
  * **Limitação frente ao AXIOM:** Permanece proprietário/caixa-preta, sem kernel de prova formal (Lean 4) e sem contrato aberto de verificação independente.

### B. Ecossistema Lean 4 MCP
* **[oOo0oOo/lean-lsp-mcp](https://github.com/oOo0oOo/lean-lsp-mcp)** *(Oliver Dressler, citado em FLARE `arXiv:2608.25220`)* & **[Numina-Lean-Agent](https://arxiv.org/pdf/2601.14027)** *(Project Numina)*
  * **Correção de autoria e capacidades:** O repositório `lean-lsp-mcp` pertence a `oOo0oOo` (Dressler) e serve de base para o **Numina-Lean-Agent** (construído sobre Claude Code + `Numina-Lean-MCP`).
  * **Importante:** O `lean-lsp-mcp` **já possui a ferramenta `lean_verify`**, que audita se uma prova que compila é insegura por usar `sorry` ou axiomas adicionais — portanto, **bloquear `sorry` e auditar axiomas em Lean não é exclusivo do AXIOM**. Além disso, oferece inspeção interativa de metas (*goals*) via LSP e integração profunda com Loogle/LeanSearch.
  * **Diferença para o AXIOM:** O `lean-lsp-mcp` é dedicado exclusivamente à escrita de provas em Lean 4; não possui motores CAS (SymPy/Sage), cálculo numérico de alta precisão (`mpmath`), resolução de EDOs, tensores ou plotagem.
* **[sandraschi/leanforge-mcp](https://github.com/sandraschi/leanforge-mcp)**
  * Implementa o padrão **"Agent A" do AlphaProof Nexus** (DeepMind, maio/2026): múltiplos agentes paralelos propõem edições de prova e o compilador Lean atua como juiz.
* **[lean-probe](https://pypi.org/project/lean-probe/0.3.1/)** & **[Lean-Prover/lean-prover](https://github.com/Lean-Prover/lean-prover)**
  * `lean-probe` fornece feedback rápido do Lean 4 como CLI, pacote Python e servidor MCP; `lean-prover` combina agente de provas em Lean 4 com benchmark de 100 problemas, busca *best-of-N*, recuperação local do Mathlib, autoformalização e servidor MCP.

### C. Servidores CAS ("Calculadoras Simbólicas e Numéricas")
* **[Jsewill/math-mcp](https://github.com/Jsewill/math-mcp):** 36 ferramentas baseadas em SymPy com saída tipada, aritmética exata/precisão arbitrária e plugins para Claude Code e `opencode`.
* **[XBP-Europe/sagemath-mcp](https://github.com/XBP-Europe/sagemath-mcp):** ~40 ferramentas sobre o **SageMath** com sessão persistente.
* **[sdiehl/sympy-mcp](https://github.com/sdiehl/sympy-mcp):** wrapper geral de SymPy com suporte opcional a relatividade geral via `einsteinpy`.
* **[andylbrummer/math-mcp](https://www.getdrio.com/mcp/io-github-andylbrummer-math-mcp/md):** servidor MCP com aceleração por GPU para álgebra simbólica/numérica, FFT e otimização.
* **[abhiphile/fermat-mcp](https://github.com/abhiphile/fermat-mcp)** (SymPy + NumPy + Matplotlib, ~16 estrelas) e `daedalus/mcp-sympy` (0 estrelas).
* **Diferencial do AXIOM nesta faixa:** nenhum desses wrappers CAS realiza verificação independente obrigatória do resultado (substituição de raízes/EDOs, FTC em integrais/derivadas, busca de contraexemplos) nem classifica o nível de garantia lógica.

---

## 3. Sistemas de Prova Formal com IA (Fora do Ecossistema MCP)

Estes sistemas representam a fronteira de prova formal autônoma. O AXIOM não compete com eles na busca neural de provas, mas atua na camada de computação verificada usada por agentes gerais:

* **Aristotle (Harmonic, [`arXiv:2510.01346`](https://arxiv.org/pdf/2510.01346v1)):** combina busca de provas em Lean 4, raciocínio matemático informal e solver dedicado de geometria; atingiu desempenho de medalha de ouro na IMO 2025 e autoformalizou provas de problemas abertos de Erdős em Lean.
* **Gauss (Math Inc.):** agente de formalização em larga escala que eliminou ~160 mil linhas de `sorry` na formalização do teorema de empacotamento de esferas em três semanas.
* **AlphaProof & AlphaProof Nexus (Google DeepMind):** sistema de aprendizado por reforço + autoformalização em Lean 4 para problemas olímpicos.
* **DeepSeek-Prover-V2** & **Kimina-Prover** *(Moonshot AI / Project Numina)*: LLMs abertos treinados com RL sobre o servidor Lean 4 para geração de provas formais completas.
* **Lean Copilot ([`arXiv:2404.12534`](https://www.arxiv.org/abs/2404.12534)):** roda inferência de LLMs nativamente dentro do Lean 4, automatizando 74,2% dos passos de prova em média.

---

## 4. Matriz Comparativa Atualizada (2026)

| Capacidade / Critério | `Jsewill/math-mcp` / `sympy-mcp` | `Wolfram Official MCP` | `oOo0oOo/lean-lsp-mcp` | `LBurny/symkit-mcp` | **AXIOM (`v0.1.x`)** |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Licença & Execução Local Offline** | ✅ (Open Source) | ❌ (Proprietário / Cloud ou Engine) | ✅ (MIT) | ✅ (Apache-2.0) | **✅ (MIT, 100% Offline-first)** |
| **Maturidade (Testes / Ferramentas)** | Média (36 tools) | **Alta (Wolfram 15)** | **Alta (Padrão Lean)** | **Alta (47 tools, 1.656 testes)** | **Inicial (21 tools, 30 suítes)** |
| **Álgebra, Cálculo, EDOs e Matrizes** | ✅ | ✅ | ❌ | ✅ | ✅ |
| **Geometria Diferencial (Tensores), Teoria dos Números, Estatística e Otimização** | Parcial | ✅ | ❌ | Parcial (Foco em física/fórmulas) | **✅ (Todos com verificador próprio)** |
| **Análise Dimensional (Unidades) & Biblioteca SQLite de Fórmulas** | ❌ | ✅ (Wolfram Units) | ❌ | **✅ (Nativa e completa)** | ❌ |
| **Inspeção Interativa de Metas Lean 4 via LSP (*Goal State*)** | ❌ | ❌ | **✅ Completa (LSP)** | ❌ | ❌ |
| **Prova Formal Lean 4 + Bloqueio de `sorry` / Auditoria de Axiomas** | ❌ | ❌ | **✅ (`lean_verify`)** | Parcial (`ring`/`field_simp` em igualdades racionais) | **✅ (`#print axioms` + cobertura obrigatória)** |
| **Verificação Independente Automática em Toda Chamada CAS** | ❌ | ❌ | N/A | Por passo na sessão (`session_verify_*`) | **✅ Automática em todas as 21 tools** |
| **Hierarquia Explícita de 6 Níveis de Garantia (`Guarantee`)** | ❌ | ❌ | ❌ | ❌ | **✅ (`formal-proof` a `unverified`)** |
| **Separação Estrita: Identidade Simbólica vs Evidência Numérica** | ❌ | ❌ | N/A | ❌ | **✅ (`exact-symbolic` vs `numerical-approximation`)** |
| **Rastreamento do Elo Mais Fraco (`chain_guarantee`)** | ❌ | ❌ | ❌ | ❌ | **✅ (`math_session`)** |

---

## 5. Posicionamento Defensável do AXIOM e Próximos Passos

Diante do cenário real de 2026, o posicionamento do AXIOM se apoia em **quatro pilares defensáveis** (sem reivindicar exclusividade onde `symkit-mcp`, `lean-lsp-mcp` ou Wolfram já atuam):

1. **Semântica Epistemológica Estrita (6 níveis de `Guarantee` + `chain_guarantee`):**
   Diferente de calculadoras CAS e mesmo do `symkit-mcp`, toda resposta do AXIOM carrega um nível formalmente ranqueado (`formal-proof`, `exact-symbolic`, `verified-substitution`, `numerical-approximation`, `heuristic`, `unverified`). Uma derivada ou integral confirmada apenas por amostragem/quadratura numérica **nunca** recebe `exact-symbolic`, e uma sessão multi-passos sempre reporta o elo mais fraco (`chain_guarantee`).
2. **Verificação Independente *Fail-Closed* em Domínios Matemáticos Amplos:**
   Cada chamada aciona automaticamente um verificador matematicamente independente do método de cálculo — incluindo compatibilidade métrica de Levi-Civita ($\nabla_\lambda g_{\mu\nu} = 0$) em tensores, FTC simbólico + quadratura em integrais, L'Hôpital/séries formais em limites, e identidades de Bézout/CRT em teoria dos números.
3. **Auditoria Completa de Provas Lean 4 (`#print axioms` + Cobertura de Declarações):**
   Enquanto o `symkit-mcp` restringe `session_certify()` ao fragmento racional via `ring`/`field_simp`, o `math_prove` do AXIOM aceita teoremas Lean 4 gerais no ambiente Lake e exige confirmação de `#print axioms` para cada teorema declarado.
4. **Caminho para Maturidade (`v0.2.0` e `v0.3.0`):**
   Para reduzir a distância de maturidade em relação ao `symkit-mcp` (1.656 testes), as prioridades imediatas do AXIOM são:
   - **`v0.2.0 — Mathematical Coverage`:** expandir massivamente os testes para singularidades, *branch cuts*, restrições de domínio, conjuntos de solução incompletos, limites direcionais e geração automática de contraexemplos, além de filtrar igualdades triviais (`x = x`) no auto-formalizador Lean.
   - **`v0.3.0 — Research Reliability`:** benchmarks reprodutíveis comparando precisão, tempo e cobertura de verificação contra `symkit-mcp`, `sympy-mcp`, SageMath e Julia.
