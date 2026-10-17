# ADR-0012: Arquitetura de Pesquisa Matemática Aberta, Millennium Research Bench e Escala de Maturidade L1–L5

- **Status**: Aceito (Accepted)
- **Data**: 2026-10-17
- **Versão do AXIOM**: v0.2.2 / v0.3.0-dev

---

## Contexto

O AXIOM evoluiu de um conjunto de 21 ferramentas matemáticas expostas via protocolo MCP para um **harness neuro-simbólico de pesquisa e verificação formal fail-closed**. O objetivo primordial do projeto não é apenas atuar como utilitário para agentes de IA ou estudantes, mas fornecer uma **infraestrutura aberta de investigação científica** para explorar a fronteira da matemática computacional, utilizando os **Sete Problemas do Prêmio do Milênio do Clay Mathematics Institute** como desafios progressivos de capacidade e confiabilidade:

1. **Hipótese de Riemann** (Análise complexa, aritmética intervalar certificada, zeros não-triviais);
2. **P versus NP** (Combinatória, reduções polinomiais, verificadores SAT/SMT e classes de complexidade);
3. **Birch e Swinnerton-Dyer** (Curvas elípticas, postos algébricos, funções $L$ e corpos finitos);
4. **Conjectura de Hodge** (Geometria algébrica, decomposição de cohomologia, classes de Lefschetz e variedades Kähler);
5. **Yang-Mills e o Gap de Massa** (Teorias de gauge não-abelianas, álgebra de Lie $\mathfrak{su}(N)$, instantons e análise funcional);
6. **Equação de Navier-Stokes** (EDPs não-lineares, incompressibilidade 3D, balanço de energia em $L^2$ e análise de blowup);
7. **Conjectura de Poincaré** (Problema de referência resolvido por G. Perelman; fluxo de Ricci com cirurgia e 3-variedades).

Essa mudança orienta o que deve ser medido: o sucesso do AXIOM não se resume a quantas ferramentas de software executam sem erro, mas a **quantos resultados matemáticos estabelecidos o motor reproduz com exatidão**, **quantas asserções falsas e adversariais ele refuta (com 0.0% de falsos positivos)**, **quantos lemas são formalizados no kernel do Lean 4** e **quão rigorosamente ele preserva o status inconclusivo perante problemas abertos**.

---

## Decisões de Arquitetura

### 1. Duas Frentes Simultâneas de Desenvolvimento
O AXIOM é formalmente estruturado em duas trilhas integradas:
- **Engenharia de Infraestrutura Matemática Confiável**: Desenvolvimento do motor simbólico, numérico, intervalar e formal (`src/axiom/`), mantendo garantias estritas, semântica ternária e 100% fail-closed.
- **Experimentação Matemática Reprodutível**: Investigação científica por meio dos Problemas do Milênio, documentando hipóteses, lemas, contraexemplos e evidências auditadas.

### 2. Os Quatro Níveis de Teste
Todo problema e hipótese sob o AXIOM é submetido a quatro níveis progressivos:
- **Nível 1 — Reproduzir Resultados Conhecidos**: Executar cálculos exatos e identidades já demonstradas na literatura com garantias `exact-symbolic` e `verified-substitution`.
- **Nível 2 — Verificar e Refutar (Controles Negativos & Adversariais)**: Introduzir violações de domínio, parâmetros espúrios e falsas soluções. O motor deve detectar falhas sem produzir certificados indevidos (`guarantee = unverified`, `status = disproven`).
- **Nível 3 — Formalizar Teoremas e Lemas**: Representar enunciados no Lean 4 / Mathlib, auditando `#print axioms` contra axiomas não-declarados e trivialidades reflexivas desprovidas de lema.
- **Nível 4 — Explorar Problemas Abertos**: Avaliar casos particulares, formular hipóteses auxiliares e pesquisar contraexemplos, garantindo retorno fail-closed controlado (`inconclusive` / `ok: false`) perante fronteiras abertas.

### 3. Escala de Maturidade da Investigação (L1 a L5)
Para distinguir rigorosamente o estágio de avanço em cada frente de pesquisa:
- **L1 (Reprodução)**: Reprodução fiel de identidades, soluções exatas e propriedades clássicas publicadas.
- **L2 (Formalização)**: Representação formal de definições, invariantes e demonstração de lemas conhecidos.
- **L3 (Investigação)**: Exploração numérica de alta precisão, varreduras combinatórias e busca sistemática de contraexemplos.
- **L4 (Contribuição Candidata)**: Formulação de lemas inéditos, algoritmos de verificação mais fortes ou refutações verificáveis.
- **L5 (Validação Científica)**: Submissão ao escrutínio da comunidade matemática internacional, revisão por pares e publicação formal (atendendo, no caso dos problemas do Clay, à exigência de validação de pelo menos dois anos na literatura aberta).

### 4. Contrato Padronizado de Investigação (`investigation.json`)
Cada problema na pasta `reports/` passa a carregar um contrato legível por máquina especificando:
- `problem`: Identificador canônico do problema.
- `official_statement`: Referência ao enunciado técnico oficial do Clay Mathematics Institute.
- `maturity_level`: Nível atual na escala L1–L5.
- `claim`: Enunciado exato, escopo e hipóteses de trabalho.
- `evidence`: Evidências simbólicas, numéricas e formais geradas.
- `verification`: Status (`proven`, `disproven`, `inconclusive`).
- `reproducibility`: Comandos de execução direta e hashes criptográficos SHA-256.

### 5. Organização da Árvore de Diretórios
A arquitetura de pesquisa passa a ser organizada em:
```text
axiom/
├── src/axiom/             # Motor matemático neuro-simbólico e verifiers
├── tests/                 # Testes automatizados do software (45 unit tests)
├── benchmarks/
│   ├── exp-0001/          # Benchmark de integridade de domínio (21 casos)
│   └── millennium/        # Suíte consolidada de avaliação dos 7 Problemas do Milênio
├── research/
│   ├── conjectures/       # Hipóteses de trabalho e enunciados em teste
│   ├── lemmas/            # Lemas auxiliares e provas Lean 4
│   └── counterexamples/   # Catálogo sistemático de refutações e contraexemplos
└── reports/               # Workspaces dos 7 Problemas do Milênio
    ├── riemann-hypothesis/
    ├── p-vs-np/
    ├── birch-and-swinnerton-dyer/
    ├── hodge-conjecture/
    ├── yang-mills-mass-gap/
    ├── navier-stokes/
    └── poincare-conjecture/
```

---

## Consequências

- **Independência de Alegações Prematuras**: O projeto gera valor acadêmico concreto em cada lema reproduzido, contraexemplo descoberto ou verificação endurecida, sem depender de alegações temerárias de solução dos problemas abertos.
- **Solidez Epistêmica**: Taxa de falsos positivos mantida estritamente em **0.0%**, com integridade fail-closed em 100% das avaliações.
- **Reprodutibilidade Total**: Todo resultado em `reports/` é reexecutável via CLI ou MCP stdio por meio de scripts `validate.py` autônomos.
