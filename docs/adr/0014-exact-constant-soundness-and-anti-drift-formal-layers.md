# ADR-0014: Solidez de Igualdade de Constantes, Partição Determinística da CLI e Rastreabilidade Anti-Drift

- **Status**: Aceito (Accepted)
- **Data**: 2026-10-17
- **Versão do AXIOM**: v0.2.3+

---

## Contexto

Durante a revisão científica detalhada após a estabilização do pipeline de CI do Millennium Bench (commit `ca8581f`), foram identificados pontos críticos de integridade matemática e reprodutibilidade:

1. **Falso Positivo Crítico em Constantes Numéricas (P0)**:
   No módulo de verificação de equivalência (`verify_equivalence`), quando uma expressão não continha símbolos livres (`free = []`) e a redução simbólica direta não zerava imediatamente a diferença, o código avaliava a magnitude numérica $|diff|$. Se essa magnitude fosse menor que a tolerância $\epsilon = 10^{-20}$, o fluxo retornava `status: proven` com garantia `numerical-approximation`.
   Como consequência, a comparação:
   $$\frac{1}{10^{30}} \stackrel{?}{=} 0$$
   resultava em $|10^{-30}| < 10^{-20}$, declarando indevidamente $\frac{1}{10^{30}} = 0$ como provado (`equivalent: true`). Este é um falso positivo clássico de tolerância numérica sobre aritmética exata.

2. **Heurística de Argumentos de Linha de Comando (P1)**:
   O encaminhamento de argumentos da CLI em scripts de validação dependia de verificação de caracteres no segundo caractere da string (`any(c.isdigit() or c in "nuptxyz" for c in arg[1:2])`). Expressões matemáticas negativas como `-sin(x)` ou `-(u*x)` eram confundidas com opções desconhecidas pelo `argparse`.

3. **Garantia de Evidências Contemporâneas nos Benchmarks (P1)**:
   A suíte de execução consolidada ignorava exceções ao tentar remover `validation.json` pré-existente e não validava se o timestamp de modificação (`mtime`) correspondia à execução que acabara de rodar, abrindo margem para reuso de arquivos residuais e aprovação indevida de suítes sem avaliações (`eval_count == 0`).

4. **Alinhamento Semântico e Specification Drift em Provas Assistidas por IA (P2)**:
   Provas assistidas por IA anunciadas recentemente (como a singularidade de Navier-Stokes com Lean 4 pela OpenAI) evidenciaram o risco de *specification drift*: o kernel Lean aceita formalmente uma prova sem `sorry`, mas a declaração formalizada pode ter enfraquecido premissas ou adicionado forças externas suaves sem correspondência com a conjectura livre de forças original. Afirmar genericamente que a auditoria de axiomas do Lean previne o desvio é incorreto: o kernel valida o teorema digitado no código, não a fidelidade da tradução semântica.

---

## Decisões de Arquitetura

### 1. Separação Estrita entre Igualdade Exata e Aproximação Numérica
No módulo `src/axiom/parsing.py`:
- Rastreamento explícito de ponto flutuante inexato (`has_inexact_floats = True`) durante a análise sintática de expressões literais (`_tree`), números decimais de alta precisão (`_HIGH_PREC_DECIMAL`), chamadas diretas a `Float()` e literais float (`_expr`).
- Exposição de `has_inexact_floats` nos metadados de domínio (`domain_info()`).

No módulo `src/axiom/verification.py`:
- Determinação antecipada do predicado `has_float`:
  ```python
  has_float = bool(
      (left_domain and left_domain.get("has_inexact_floats"))
      or (right_domain and right_domain.get("has_inexact_floats"))
      or (isinstance(diff, sp.Basic) and diff.has(sp.Float))
      or (isinstance(left, sp.Basic) and left.has(sp.Float))
      or (isinstance(right, sp.Basic) and right.has(sp.Float))
  )
  ```
- Bloqueio de absorção: `symbolic_ok = (not has_float) and _is_symbolic_zero(diff)`. Se houver qualquer entrada float inexata, a simplificação algébrica nunca pode atribuir `EXACT_SYMBOLIC` ou `proven`.
- Reordenação da verificação: o ramo `if has_float:` é avaliado **antes** de `if symbolic_ok:`. Expressões como `0.1 + 1/10^20` vs `0.1` retornam categoricamente `status: "approximately_equal"`, `equivalent: false`, `approximately_equal: true`, com garantia `Guarantee.UNVERIFIED`.
- Para constantes exatas (sem float), qualquer resíduo não-nulo resulta em `disproven` (`status: "disproven"`).

No módulo `src/axiom/core.py`:
- `Axiom.compare()` trata o veredito `approximately_equal` com `equivalent: false`, `relation: \approx`, e registra tolerância e erro nos metadados.

### 2. Partição Determinística de Argumentos da CLI
Em `reports/*/validate.py` e rotinas correlatas:
- Eliminação de qualquer heurística baseada em caracteres individuais;
- Definição estrita de conjuntos canônicos `KNOWN_OPTIONS_WITH_ARG` (incluindo `--canonical`, `--alignment`, `--hypotheses`) e `KNOWN_FLAGS_NO_ARG`;
- Inserção compulsória do delimitador padrão `--` antes dos argumentos posicionais quando presentes, assegurando que expressões negativas arbitrárias (como `-sin(x)`, `-4*nu*pi^2*exp(-4*nu*t)`) sejam tratadas inequivocamente como operandos matemáticos pelo `argparse`.

### 3. Isolamento e Contemporaneidade Estrita de Evidências
- Suporte a injeção de caminho via variável de ambiente `AXIOM_VALIDATION_OUT` em todas as rotinas `reports/*/validate.py`:
  ```python
  OUTPUT = Path(os.environ.get("AXIOM_VALIDATION_OUT") or Path(__file__).with_name("validation.json"))
  ```
- Em `benchmarks/millennium/run_millennium_bench.py`:
  - Cada suíte de validação é executada em diretório temporário efêmero (`tempfile.mkdtemp`), definindo `AXIOM_VALIDATION_OUT` para isolamento total contra stale cache, locks de SO e concorrência;
  - Após a verificação de contemporaneidade e integridade, as evidências são consolidadas em `reports/<problema>/validation.json`;
  - Rejeição obrigatória de suítes vazias: `eval_count > 0` passa a ser condição estrita para aprovação (`suite_ok`).

### 4. Manifesto Executável de Integridade Epistêmica contra *Specification Drift*
No núcleo matemático (`Axiom.prove`), CLI (`axiom prove --canonical ... --alignment ... --hypotheses ...`) e MCP Server (`math_prove`):
Implementação de registro executável com três camadas estruturadas em `formal_manifest`:
1. **Validade de Kernel (`kernel_validity`)**: Checagem formal pelo Lean 4 com auditoria de axiomas (`#print axioms`), validando ausência de `sorry` e axiomas não confiáveis;
2. **Auditoria de Hipóteses (`assumptions_audit`)**: Confrontação entre hipóteses declaradas (`declared_hypotheses`) e detectadas na sintaxe do teorema, sinalizando premissas implícitas ou não justificadas;
3. **Alinhamento de Especificação (`spec_alignment`)**: Confrontação explícita entre enunciado canônico (`canonical_statement`) e o escopo formalizado (`formal_statement`), com classificação semântica (`congruent`, `scoped_forced_variant`, `tautology_control`, `unspecified`). Tautologias e variantes não alinhadas têm prova rejeitada (`Guarantee.UNVERIFIED`, `passed: false`).

### 5. Derivação Dinâmica dos Campos de Navier-Stokes
Em `reports/navier-stokes/validate.py`:
- Incompressibilidade ($\nabla \cdot \mathbf{u} = 0$) é verificada diferenciando diretamente os componentes de velocidade $u(x,y,t)$ e $v(x,y,t)$ via `axiom differentiate`, somando os gradientes espaciais calculados;
- Taxa de dissipação viscosa $D(t) = \nu \int_\Omega |\nabla \mathbf{u}|^2 d\Omega$ e derivada temporal da energia cinética $dE/dt$ são compostas via pipelines encadeados de `differentiate` e `integrate`;
- Inclusão da sonda anti-drift em Lean 4 para variantes com força externa (`scoped_forced_variant`).

---

## Consequências

- **Falsos Positivos de Ponto Flutuante Eliminados**: Absorções numéricas infinitesimais como `0.1 + 1/10^20 vs 0.1` jamais recebem `EXACT_SYMBOLIC` ou `proven`.
- **Robustez CLI**: Linha de comando aceita qualquer expressão matemática iniciada por sinal negativo sem falhas de sintaxe.
- **Isolamento de Evidências no CI**: Benchmarks executam em sandbox temporal com sincronização limpa para git.
- **Rigor na Relação AXIOM–Lean**: Provas formais geram manifestos de 3 camadas com auditoria de premissas e conformidade semântica contra desvios de especificação.
- **Taxa Fail-Closed Global Mantida em 100%**: 103/103 critérios aprovados nos 7 Problemas do Milênio com 0 falsos positivos.
