# Catálogo de GitHub Agent Skills para o Chronokairo AXIOM

*Pesquisa e Especificação de 18 de Outubro de 2026 · Skills Públicas para Matemática, Provas Formais, Pesquisa Científica e Engenharia de Software*

---

## 1. Visão Geral e Princípio de Separação

O Chronokairo AXIOM atua como um laboratório de investigação matemática orientado pelo paradigma **REA (Reverse Engineer Anything)** — *Investigate Mathematics with Agents* ([ADR-0019](adr/0019-mathematical-investigation-layer-rea-paradigm.md)).

Com o crescimento do ecossistema de **Agent Skills** (protocolos e instruções em Markdown que capacitam agentes como Claude Code, Codex, Antigravity, Copilot Workspace e subagentes autônomos), este catálogo organiza as habilidades externas e internas recomendadas para maximizar a capacidade investigativa do AXIOM.

> [!IMPORTANT]
> **O Princípio de Separação Epistêmica ([ADR-0020](adr/0020-agent-skills-architecture-and-governance.md)):**
> **Skills são instruções e protocolos cognitivos para agentes, NÃO motores matemáticos ou provas.**
> Uma skill instrui o agente a verificar, refutar, estruturar e duvidar. No entanto, o certificado matemático (`formal-proof`, `exact-symbolic`, `verified-substitution`, `numerical-approximation`) é **exclusivamente emitido pelo kernel formal (Lean 4) ou pelos motores de computação algébrica (SymPy, mpmath, Julia)** via kernel interativo. Nenhuma instrução em linguagem natural pode conceder garantia matemática por si só.

---

## 2. Taxonomia Oficial de Skills do AXIOM

As skills próprias e adaptadas do repositório estão estruturadas em 5 pilares funcionais sob [`skills/`](../skills/):

```
skills/
├── README.md                          # Índice mestre e guia de uso
├── mathematics/                       # Skill fundamental de cálculo, álgebra e verificação MCP
├── toolchain-management/              # Detecção e instalação de toolchains (Lean, Lake, Julia)
│
├── research/                          # Investigação matemática em aberto
│   ├── math-research/                 # Condução de investigações, hipóteses e barreiras
│   └── proof-auditing/                # Auditoria de demonstrações informais (LaTeX) e gaps
│
├── formal/                            # Provas interativas e alinhamento de especificação
│   ├── lean4/                         # Kernel Lean 4, Lake, #print axioms, auditoria sorryAx
│   ├── writing-lean-proofs/           # Estruturação modular de lemas e táticas Mathlib
│   └── statement-alignment/           # Anti-drift: alinhamento formal vs enunciado canônico
│
├── computational/                     # Experimentação numérica e EDPs
│   ├── uncertainty-and-units/         # Análise dimensional e propagação de incerteza
│   └── fluidsim/                      # Simulação de fluidos, Taylor-Green e energia cinética
│
├── verification/                      # Testes adversariais e conformidade de contratos
│   ├── property-based-testing/        # Teste baseado em propriedades e busca de contraexemplos
│   ├── mutation-testing/              # Teste de mutação em especificações matemáticas
│   └── spec-to-code-compliance/       # Validação estrita entre contratos matemáticos e código
│
└── scientific/                        # Documentação acadêmica e ciência aberta
    ├── literature-review/             # Revisão bibliográfica sistemática e corpus de teoremas
    ├── citation-verification/         # Validação de referências, DOIs e prevenção de alucinações
    └── reproducibility-statement/     # Dossiês reprodutíveis e manifestos SHA-256
```

---

## 3. Catálogo de Coleções Públicas no GitHub

### A. Formalização e Assistentes de Provas (P0 — Provas)

| Skill / Repositório | Repositório de Origem | Aplicação no AXIOM | Ferramentas MCP Relacionadas |
| :--- | :--- | :--- | :--- |
| **lean4** | [`cameronfreer/lean4-skills`](https://github.com/cameronfreer/lean4-skills) | Depurar erros de compilação Lean 4, inspecionar dependências com `#print axioms`, rastrear `sorryAx`. | `math_prove`, `mathlib_search` |
| **lean-formalization** | [`VeryMath/AI4Math-Lean-Agents`](https://github.com/VeryMath/AI4Math-Lean-Agents) | Traduzir afirmações informais em proposições tipadas Lean 4 e consertar táticas quebradas. | `math_prove`, `math_parse` |
| **writing-lean-proofs** | [`trailofbits/skills`](https://github.com/trailofbits/skills) | Estruturar bibliotecas compatíveis com Mathlib, evitando lemas monolíticos frágeis. | `math_prove` |
| **lean-setup** | [`VeryMath/AI4Math-Lean-Agents`](https://github.com/VeryMath/AI4Math-Lean-Agents) | Configuração de ambientes reproduzíveis com `elan`, `lake` e Mathlib cache. | `math_doctor`, `toolchain-management` |
| **rocq** | [`LLM4Rocq/rocq-skills`](https://github.com/LLM4Rocq/rocq-skills) | Exploração e formalização com Coq/Rocq como assistente alternativo. | `math_prove` (extensão) |

### B. Investigação e Raciocínio Matemático (P0 — Pesquisa)

| Skill / Repositório | Repositório de Origem | Aplicação no AXIOM | Ferramentas MCP Relacionadas |
| :--- | :--- | :--- | :--- |
| **math-research** | [`jmf-enigma/math-research`](https://github.com/jmf-enigma/math-research) | Conduzir pesquisa em problemas em aberto, mapear barreiras de complexidade e registrar sessões. | `math_session`, `math_explore` |
| **mathematical-proof-auditing** | [`NNHieu/math_auditing_examples`](https://github.com/NNHieu/math_auditing_examples) | Auditar artigos e demonstrações LaTeX para localizar saltos lógicos, circularidades ou premissas implícitas. | `math_verify`, `math_compare` |
| **paper-to-skill-extractor** | [`ConanXu-math/paper-to-skill-extractor`](https://github.com/ConanXu-math/paper-to-skill-extractor) | Extrair técnicas de demonstração e lemas intermediários de artigos científicos. | `math_explain`, `math_session` |

### C. Álgebra Computacional, EDPs e Física (P1 — Computacional)

| Skill / Repositório | Repositório de Origem | Aplicação no AXIOM | Ferramentas MCP Relacionadas |
| :--- | :--- | :--- | :--- |
| **sympy** | [`K-Dense-AI/scientific-agent-skills`](https://github.com/K-Dense-AI/scientific-agent-skills) | Manipulação simbólica avançada, EDOs e simplificações polinomiais. | `math_simplify`, `math_solve`, `math_diff`, `math_integrate` |
| **uncertainty-and-units** | [`K-Dense-AI/scientific-agent-skills`](https://github.com/K-Dense-AI/scientific-agent-skills) | Checagem de homogeneidade dimensional, escalas físicas e incertezas numéricas. | `math_evaluate`, `math_compare` |
| **fluidsim** | [`K-Dense-AI/scientific-agent-skills`](https://github.com/K-Dense-AI/scientific-agent-skills) | Dinâmica de fluidos, vórtice de Taylor-Green e dissipação de Navier-Stokes. | `math_differentiate`, `math_compare`, `math_plot` |
| **openpiv** | [`K-Dense-AI/scientific-agent-skills`](https://github.com/K-Dense-AI/scientific-agent-skills) | Análise de velocimetria por imagem de partículas em fluidos. | `math_matrix`, `math_statistics` |
| **networkx** | [`K-Dense-AI/scientific-agent-skills`](https://github.com/K-Dense-AI/scientific-agent-skills) | Teoria dos grafos, sensibilidade Booleana e análise de Huang matrices (P vs NP). | `math_matrix`, `math_solve` |

### D. Verificação, Segurança e Testes Adversariais (P0 — Verificação)

| Skill / Repositório | Repositório de Origem | Aplicação no AXIOM | Ferramentas MCP Relacionadas |
| :--- | :--- | :--- | :--- |
| **property-based-testing** | [`trailofbits/skills`](https://github.com/trailofbits/skills) | Testar invariantes funcionais contra espaço amostral estocástico denso. | `math_compare`, `math_verify` |
| **mutation-testing** | [`trailofbits/skills`](https://github.com/trailofbits/skills) | Injetar mutações intencionais em teoremas e equações para auditar se o sistema falha fechado. | `math_compare`, `math_prove` |
| **spec-to-code-compliance** | [`trailofbits/skills`](https://github.com/trailofbits/skills) | Verificar correspondência exata entre o contrato formal canônico e o código executado. | `math_prove`, `math_verify` |
| **verification-before-completion** | [`obra/superpowers`](https://github.com/obra/superpowers) | Proibir agentes de encerrar tarefas sem reexecução e aprovação dos testes locais. | `math_doctor`, `math_session` |
| **systematic-debugging** | [`obra/superpowers`](https://github.com/obra/superpowers) | Diagnosticar discrepâncias entre saídas de CAS simbólicos e motores numéricos. | `math_compare`, `math_explore` |

### E. Documentação, Citações e Reprodutibilidade (P1 — Ciência Aberta)

| Skill / Repositório | Repositório de Origem | Aplicação no AXIOM | Ferramentas MCP Relacionadas |
| :--- | :--- | :--- | :--- |
| **literature-review** | [`K-Dense-AI/scientific-agent-skills`](https://github.com/K-Dense-AI/scientific-agent-skills) | Estruturação de revisões da literatura com rastreabilidade de teses e teoremas. | `math_session`, `mathlib_search` |
| **citation-verification** | [`KalarisLabs/research-agent-skills`](https://github.com/KalarisLabs/research-agent-skills) | Auditoria de bibliografias BibTeX, validação de DOI/arXiv e eliminação de citações fantasmas. | `math_session` |
| **reproducibility-statement** | [`KalarisLabs/research-agent-skills`](https://github.com/KalarisLabs/research-agent-skills) | Geração de declarações de reprodutibilidade com hashes SHA-256 e comandos exatos de reexecução. | `math_session` (action="export") |
| **bibtex-hygiene** | [`KalarisLabs/research-agent-skills`](https://github.com/KalarisLabs/research-agent-skills) | Normalização e desduplicação de arquivos de referências. | `math_session` |

---

## 4. O Checklist dos 12 Starter Skills do AXIOM

Para implantação imediata, foram selecionadas e customizadas 12 skills fundamentais integradas à CLI e MCP do AXIOM:

1. [x] **`formal/lean4`**: Condução e auditoria de provas interativas em Lean 4 com verificação estrita de axiomas.
2. [x] **`formal/writing-lean-proofs`**: Decomposição e estruturação modular de provas formais com táticas Mathlib.
3. [x] **`formal/statement-alignment`**: Auditoria anti-drift para prevenir que teoremas parciais ou forçados sejam promovidos a provas canônicas.
4. [x] **`research/math-research`**: Protocolo de investigação de problemas difíceis, preservando premissas e registrando falhas.
5. [x] **`research/proof-auditing`**: Identificação sistemática de furos lógicos, premissas não enunciadas e circularidades em artigos.
6. [x] **`verification/property-based-testing`**: Verificação de invariantes algébricas e geração automática de contraexemplos.
7. [x] **`verification/mutation-testing`**: Auditoria dos testes do AXIOM contra mutações sintáticas e semânticas.
8. [x] **`verification/spec-to-code-compliance`**: Garantia de correspondência exata entre enunciados e contratos matemáticos.
9. [x] **`computational/uncertainty-and-units`**: Verificação dimensional e propagação de limites de erro em modelos físicos.
10. [x] **`computational/fluidsim`**: Experimentação computacional com dinâmica de fluidos e equações de Navier-Stokes.
11. [x] **`scientific/literature-review`**: Mapeamento do estado da arte e taxonomia de abordagens prévias.
12. [x] **`scientific/citation-verification`**: Checagem de autenticidade de referências e citações.
13. [x] **`scientific/reproducibility-statement`**: Emissão de relatórios reprodutíveis com proveniência criptográfica.

---

## 5. Como Usar as Skills com Agentes de IA

Ao interagir com o Chronokairo AXIOM através de agentes autônomos (como Claude Code, Codex, Antigravity, Copilot), o agente lê o arquivo `SKILL.md` relevante e segue rigorosamente os protocolos:

1. **Ativação**: O agente consulta `skills/README.md` ou a subpasta específica do pilar (`skills/formal/`, `skills/research/`, etc.).
2. **Execução de Ferramentas**: As instruções da skill instruem o agente a invocar as ferramentas MCP (`math_solve`, `math_prove`, `math_compare`, `math_session`, etc.) ou a CLI (`axiom prove`, `axiom session`).
3. **Checagem de Garantia**: O agente inspeciona o campo `guarantee` retornado pelo AXIOM:
   - Se for `formal-proof`, relata como demonstrado formalmente.
   - Se for `exact-symbolic` ou `verified-substitution`, relata como equivalente algébrico verificado.
   - Se for `numerical-approximation`, declara as margens de tolerância e limitações.
   - Se for `unverified` ou `heuristic`, declara como conjectura aberta, hipótese refutada ou prova incompleta.
