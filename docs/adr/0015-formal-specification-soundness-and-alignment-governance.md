# ADR-0015: Solidez de Especificação Formal, Auditoria Semântica de Alinhamento e Derivação Estrita de Dissipação

- **Status**: Aceito (Accepted)
- **Data**: 2026-10-17
- **Versão do AXIOM**: v0.2.4

---

## Contexto

Durante a revisão científica detalhada após o commit `73308d7` (v0.2.3+), foram identificadas vulnerabilidades conceituais na verificação de alinhamento formal de especificações e na integridade de evidências do Millennium Research Bench:

1. **Vulnerabilidade de Especificação Não Auditada (Specification Drift - P0)**:
   A versão anterior confiava cegamente no argumento `--alignment` passado pelo usuário ou por um agente autônomo. Um modelo de IA ou usuário podia submeter um teorema trivial como `x + 0 = x` ou `examples/theorems.lean` (aritmética elementar de `Nat`), declarar `--alignment congruent` contra a *Hipótese de Riemann* ou *Navier-Stokes*, e o sistema registrava `status: congruent` e `is_aligned: true` no manifesto formal. Provas formais recentes geradas por IA evidenciam o risco de demonstrar enunciados enfraquecidos ou variantes não-canônicas (como Navier-Stokes com forças externas suaves) alegando terem resolvido o problema canônico aberto.

2. **Atribuição Indevida de Validade de Kernel em SymPy (P0)**:
   Quando `prove()` era invocado com `engine="sympy"`, o sistema marcava `kernel_validity.verified = True`. No entanto, o SymPy é um sistema de computação algébrica simbólica (CAS), não um assistente de prova interativo baseado em teoria de tipos com kernel lógico estrito como o Lean 4. Indicar kernel verificado para SymPy distorcia a hierarquia de garantias formais do AXIOM.

3. **Incompletude na Auditoria de Hipóteses (P1)**:
   Quando um chamador não declarava hipóteses (`declared_hypotheses = []`), mas o código/assinatura do teorema continha premissas explícitas (ex.: `(a b : Nat)`), a auditoria marcava `status: clean`. Premissas não declaradas passavam desapercebidas, violando o princípio de transparência de hipóteses formais.

4. **Risco de Fallback Residual no Benchmark (P1)**:
   Em `benchmarks/millennium/run_millennium_bench.py`, havia um fallback para `repo_validation_json` caso o arquivo temporário isolado não existisse. Se um teste falhasse em gerar sua saída isolada, o benchmark podia inspecionar o arquivo antigo do repositório, quebrando o isolamento estrito.

5. **Inserção Manual da Dissipação Viscosa de Taylor-Green (P2)**:
   No relatório de Navier-Stokes, a taxa analítica $4\nu\pi^2e^{-4\nu t}$ era injetada diretamente na verificação de balanço, em vez de ser derivada dinamicamente por integração espacial dos gradientes de velocidade.

---

## Decisões de Arquitetura

### 1. Desacoplamento entre Alinhamento Declarado e Alinhamento Verificado (`spec_alignment`)

No módulo `src/axiom/core.py`, foi implementado um auditor semântico independente `_audit_specification_alignment`:
- **Ontologia de Domínios Canônicos**: O dicionário `_CANONICAL_DOMAINS` mapeia os 7 Problemas do Milênio do Clay Mathematics Institute:
  - Riemann Hypothesis (`zeta`, `critical line`, `complex zeros`)
  - Navier-Stokes (`velocity`, `viscosity`, `incompressible`, `laplacian`, `forcing`)
  - Birch and Swinnerton-Dyer (`elliptic curve`, `rank`, `l-function`, `sha`)
  - Hodge Conjecture (`hodge`, `cohomology`, `algebraic cycle`, `kahler`)
  - P vs NP (`complexity`, `turing`, `np-complete`, `polynomial time`)
  - Poincaré Conjecture (`manifold`, `homeomorphic`, `ricci`, `sphere`)
  - Yang-Mills (`gauge`, `mass gap`, `quantum`, `compact Lie group`)
- **Separação Estrita de Campos**: O manifesto formal registra:
  - `declared_alignment`: a intenção declarada pelo chamador;
  - `verified_alignment`: o veredito auditado semanticamente pelo motor;
  - `is_aligned`: booleano estrito indicando compatibilidade ontológica com o problema;
  - `congruent`: booleano indicando equivalência exata ao problema canônico;
  - `audit_method` e `scope_notes`: rastreabilidade e justificativa formal.
- **Rejeição Automática de Mismatches**: Se uma expressão formal (como `x + 0 = x` ou `examples/theorems.lean`) for associada a um Problema do Milênio sem correspondência com sua ontologia, o auditor define:
  ```python
  verified_alignment = "unaligned"
  is_aligned = False
  congruent = False
  audit_method = "domain_ontology_mismatch"
  ```
  Isso rebaixa a garantia para `Guarantee.UNVERIFIED` e define `verification.passed = False`.
- **Rastreabilidade de Variantes de Forçamento (Anti-Drift)**:
  Se o teorema formaliza um modelo com força externa (como em `examples/navier_stokes_forced.lean`), o auditor identifica:
  ```python
  verified_alignment = "scoped_forced_variant"
  is_aligned = True
  congruent = False
  audit_method = "domain_forcing_variant_audit"
  ```
  Impedindo que variantes com forças externas sejam promovidas a provas da conjectura canônica não-forçada.

### 2. Gating Rígido de Validade de Kernel para SymPy

No método `Axiom.prove()`:
- Quando `engine="sympy"`, `kernel_validity["verified"]` é categoricamente fixado em `False`:
  ```python
  kernel_validity = {
      "verified": False,
      "runner": "sympy",
      "status": "not_applicable",
      "detail": "SymPy algebraic verification; formal proof assistant kernel (e.g. Lean 4) was not executed",
      ...
  }
  ```
- SymPy realiza manipulação e equivalência algébrica, mas não substitui a verificação formal type-theoretic de assistentes de prova interativos.

### 3. Auditoria Fail-Closed de Hipóteses Não-Declaradas

No analisador de hipóteses de `Axiom.prove()`:
- Se `detected_hypotheses` contiver parâmetros/hipóteses inferidos da assinatura formal ou variáveis livres de SymPy, e o usuário fornecer `declared_hypotheses = []` (ou não declarar):
  ```python
  assumptions_audit["implicit_hypotheses"] = list(detected_hypotheses)
  assumptions_audit["implicit_hypotheses_flagged"] = True
  assumptions_audit["status"] = "warning_undeclared_hypotheses"
  ```
- O status `clean` é reservado exclusivamente para quando não há hipóteses detectadas ou quando todas as detectadas foram explicitamente declaradas.

### 4. Zero-Fallback e Isolamento Estrito no Benchmark Runner

Em `benchmarks/millennium/run_millennium_bench.py`:
- O runner exige compulsoriamente a existência contemporânea de `isolated_validation_json`.
- Foi eliminado o operador de fallback (`if isolated_validation_json.exists() else repo_validation_json`). Se a suíte isolada não gerar evidências, o benchmark falha imediatamente em fail-closed.

### 5. Derivação Simbólica Completa da Dissipação Viscosa de Navier-Stokes

Em `reports/navier-stokes/validate.py`:
- As componentes do gradiente de velocidade de Taylor-Green $\partial_x u, \partial_y u, \partial_x v, \partial_y v$ são elevadas ao quadrado e somadas:
  $$|\nabla \mathbf{u}|^2 = (\partial_x u)^2 + (\partial_y u)^2 + (\partial_x v)^2 + (\partial_y v)^2$$
- Integração simbólica em $x \in [0, 2\pi]$ produz $2\pi e^{-4\nu t}\sin^2(y) + 2\pi e^{-4\nu t}\cos^2(y)$;
- Segunda integração simbólica em $y \in [0, 2\pi]$ produz exatamente $4\pi^2 e^{-4\nu t}$;
- A taxa de dissipação total é construída como $\nu \cdot 4\pi^2 e^{-4\nu t}$;
- O balanço dinâmico $\frac{dE}{dt} + D(t) \equiv 0$ é verificado com garantia `exact-symbolic`, completamente derivado a partir do campo de velocidades sem injeção analítica externa manual.
- Adicionado critério positivo `dissipation_spatial_integral_exact` e controle negativo `lean_unaligned_mismatch_refuted`.

---

## Consequências

- **Imunidade contra Spoofing de Alinhamento**: Nenhum agente de IA ou script pode induzir o AXIOM a certificar provas de Problemas do Milênio manipulando a flag `--alignment`.
- **Hierarquia Científica Honesta**: Usuários e sistemas clientes de MCP recebem manifestos formais claros separando o que foi provado pelo kernel Lean, o que foi simplificado por SymPy, quais hipóteses foram assumidas e a qual classe ontológica o teorema realmente pertence.
- **Rigor Matemático Estrito**: Todos os cálculos dos benchmarks Millennium passam a ser derivados operacionalmente de princípios primeiros dentro do próprio motor.
