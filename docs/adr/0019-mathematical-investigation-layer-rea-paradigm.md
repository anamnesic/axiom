# ADR-0019: Camada de Investigação Matemática — Portando o Paradigma REA para a Matemática

- **Status**: Aceito (Accepted)
- **Data**: 2026-10-18
- **Autores**: Equipe de Arquitetura AXIOM & Chronokairo Research
- **Inspirado em**: [morluto/rea (Reverse Engineer Anything)](https://github.com/morluto/rea)

---

## Contexto & Declaração de Posicionamento

Historicamente, softwares matemáticos dividem-se em duas categorias:
1. **Sistemas de Computação Algébrica (CAS)** como SymPy, SageMath e Mathematica, voltados para resolução, diferenciação e simplificação.
2. **Assistentes de Prova Interativos (ITP)** como Lean 4, Coq e Isabelle, focados na teoria de tipos e verificação formal de teoremas.

Contudo, na era dos agentes de inteligência artificial autônomos, o maior desafio não é apenas resolver uma equação isolada, mas **investigar uma afirmação matemática complexa**: decompor conjecturas em subproblemas, rastrear grafos de dependências de lemas, mapear barreiras lógicas, coletar evidências reproduzíveis e catalogar lacunas honestas sem alucinar passos dedutivos.

Essa dinâmica é idêntica à de **Engenharia Reversa**:
- O projeto **REA (Reverse Engineer Anything)** estabeleceu um paradigma pioneiro para engenharia reversa com agentes: não tenta substituir ferramentas de baixo nível (Ghidra, IDA Pro, Hopper, GDB), mas fornece o harness orquestrador para decompor binários, construir grafos de chamadas e acumular evidências verificáveis.
- O **AXIOM** adota explicitamente essa mesma filosofia para a matemática:
  > **REA**: *Reverse engineer anything* $\to$ Entender como um sistema funciona, a partir de artefatos e evidências.  
  > **AXIOM**: *Investigate mathematics* $\to$ Entender uma afirmação matemática, investigando suas estruturas, hipóteses, barreiras e provas.

---

## Equivalência Arquitetural: REA $\leftrightarrow$ AXIOM

| Conceito no REA (Engenharia Reversa) | Equivalente no AXIOM (Pesquisa Matemática) |
| :--- | :--- |
| **Binário, aplicativo ou comportamento** | Equação, conjectura, teorema ou modelo |
| **Decompilação & Desmontagem** | Decomposição formal em lemas, binders e tipos |
| **Call Graph & CFG (Fluxo de Controle)** | Proof Dependency Graph (DAG de lemas e premissas) |
| **Análise Estática & Simbólica** | Análise algébrica, redução de invariantes e auditoria FTC |
| **Análise Dinâmica & Fuzzing** | Amostragem gaussiana complexa e busca de contraexemplos |
| **Rastreamento de Funções** | Rastreamento de passos de demonstração |
| **Comparação de Implementações** | Comparação de formalizações e métodos de prova |
| **Ghidra, Hopper, IDA, GDB** | SymPy, mpmath, SageMath, Julia, Lean 4 / Mathlib |
| **Evidence Bundle (`get_evidence_bundle`)** | Dossiê de Evidências com certificados, logs e hashes SHA-256 |
| **Unknowns (`list_unknowns`)** | **Unknown Ledger**: catálogo de lacunas e obrigações de prova |

---

## Decisões de Arquitetura

### 1. Invariante Epistêmica: *Semantic Anti-Drift*

Diferente do software onde testes dinâmicos de I/O comprovam equivalência comportamental, na matemática existe o risco crítico de **Specification Drift**: demonstrar um enunciado enfraquecido e alegar ter resolvido o problema canônico.

O AXIOM torna obrigatório o rastreamento formal estrito:
$$\text{Problema Canônico} \xrightarrow[\text{Audit}]{\text{Alinhamento}} \text{Subproblemas} \xrightarrow[\text{DAG}]{\text{Implicação}} \text{Lemas} \xrightarrow[\text{Kernel}]{\text{Demonstração}} \text{Evidências}$$

Se um lema não possui equivalência formal demonstrada com o enunciado canônico, ele é catalogado estritamente como `candidate` ou lema auxiliar, e a afirmação principal permanece no `Unknown Ledger`.

### 2. As 8 Primitivas da Camada de Investigação (`Investigation Layer`)

Em vez de expandir aleatoriamente ferramentas utilitárias, o AXIOM adiciona as seguintes 8 primitivas de alto nível para agentes e pesquisadores:

1. `math_investigate`: Inicializa um dossiê persistente com UUID, enunciado alvo formalizado e escopo de domínios.
2. `math_analyze_claim`: Decompõe a afirmação em variáveis livres, hipóteses implícitas, tipos de dados e condições de contorno.
3. `math_trace_dependencies`: Constrói e audita o DAG de lemas necessários, separando integridade estrutural de implicação lógica demonstrada.
4. `math_find_counterexample`: Executa fuzzing algébrico com amostras gaussianas complexas e polos para tentar refutar ativamente a conjectura.
5. `math_compare_proofs`: Compara diferentes métodos de demonstração (ex.: analítico vs formal Lean) identificando hipóteses adicionais.
6. `math_list_unknowns`: O **Unknown Ledger** — relata lacunas abertas, furos lógicos (`sorry`), axiomas não verificados e hipóteses pendentes.
7. `math_get_evidence_bundle`: Exporta pacote imutável contendo versões dos motores, logs de kernel, entradas, sementes e hashes de verificação.
8. `math_export_investigation`: Gera um dossiê completo e reproduzível com `REPORT.md`, diagramas Mermaid e certificados de revalidação.

### 3. Estrutura do Dossiê de Investigação (`.axiom/investigations/<id>/`)

Cada investigação persistente é mantida isoladamente no sistema de arquivos:
```text
.axiom/investigations/<investigation_id>/
├── spec.json           # Especificação formalizada do problema e escopo
├── graph.json          # Proof Dependency Graph com nós e arestas auditadas
├── unknowns.json       # Unknown Ledger (lacunas e proof obligations)
├── evidence/           # Logs do Lean 4 (#print axioms), saídas simbólicas e numéricas
├── bundle.json         # Pacote atômico com hashes de proveniência
└── REPORT.md           # Dossiê executivo completo para agentes e pesquisadores
```

---

## Consequências e Posicionamento

- **Novo Posicionamento**:
  > **Chronokairo AXIOM — Investigate Mathematics with Agents.**  
  > *One MCP for mathematical investigation, computation, and verification.*
- **Função dos Problemas do Milênio**: Deixam de ser "alvos a serem resolvidos ingenuamente" e passam a ser os bancos de teste mais rigorosos do mundo para validar a capacidade do motor em identificar barreiras, provar lemas periféricos e catalogar honestamente o que falta demonstrar.
- **Implementação**: A estrutura de documentação, esquemas e contratos é estabelecida na v0.2.7/v0.3.0, com implementações incrementais e testes automatizados.
