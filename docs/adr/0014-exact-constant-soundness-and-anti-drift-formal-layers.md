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
No módulo `src/axiom/verification.py`:
- Para expressões sem símbolos livres (`not free`):
  1. Se `_is_symbolic_zero(diff)` for satisfeito, a identidade exata é declarada como `proven` com garantia `EXACT_SYMBOLIC`.
  2. Se as expressões contiverem ponto flutuante (`sp.Float`) e a diferença for menor que a tolerância $\epsilon$, o resultado é categorizado como `approximately_equal` (`equivalent: false`, `approximately_equal: true`, garantia `UNVERIFIED`), sem jamais ser promovido a `proven`.
  3. Se as expressões forem exatas (inteiros, racionais, números algébricos, constantes simbólicas como $\pi, e$) e não reduzirem identicamente a zero, sua não-nulidade é auditada de forma exata (`is_nonzero`, `is_positive`, `is_negative` ou avaliação em alta precisão com dígitos estáveis). O veredito é categoricamente `disproven` (`status: "disproven"`, `equivalent: false`).
  4. Nenhuma proximidade numérica em ponto flutuante tem autoridade para certificar igualdade exata entre constantes.

No módulo `src/axiom/core.py`:
- `Axiom.compare()` trata explicitamente o estado `approximately_equal`:
  - `status: "approximately_equal"`;
  - `equivalent: false`;
  - `relation: \approx`;
  - metadados registram `tolerance` e `max_error`.

### 2. Partição Determinística de Argumentos da CLI
Em `reports/navier-stokes/validate.py` e rotinas correlatas:
- Eliminação de qualquer heurística baseada em caracteres;
- Definição estrita de conjuntos canônicos `KNOWN_OPTIONS_WITH_ARG` e `KNOWN_FLAGS_NO_ARG`;
- Inserção compulsória do delimitador padrão `--` antes dos argumentos posicionais quando presentes, assegurando que expressões negativas arbitrárias (como `-sin(x)`, `-4*nu*pi^2*exp(-4*nu*t)`) sejam tratadas inequivocamente como operandos matemáticos pelo `argparse`.

### 3. Isolamento e Contemporaneidade Estrita de Evidências
Em `benchmarks/millennium/run_millennium_bench.py`:
- Tentativa de remoção de `validation.json` anterior com fallback de renomeação caso ocorram locks no sistema operacional; se a remoção/isolamento falhar, a execução aborta fail-closed;
- Verificação do timestamp de modificação (`mtime >= start_time - 1.0s`), rejeitando arquivos não gerados pela execução corrente;
- Rejeição obrigatória de suítes vazias: `eval_count > 0` passa a ser condição estrita para aprovação (`suite_ok`).

### 4. Camadas de Integridade Epistêmica contra *Specification Drift*
Nos relatórios de pesquisa e documentação científica (`related-work.md`, `reports/navier-stokes/REPORT.md`), a validação formal passa a ser explicitamente estruturada em três camadas ortogonais:
1. **Validade de Kernel (`kernel_validity`)**: Checagem formal pelo Lean 4 com auditoria de axiomas (`#print axioms`), assegurando ausência de `sorry` e tautologias triviais (`rfl`);
2. **Auditoria de Hipóteses e Domínio (`assumptions_audit`)**: Verificação explícita de consistência e minimalidade das premissas analíticas (impedindo suposições tácitas de regularidade);
3. **Correspondência de Especificação (`spec_alignment`)**: Rastreamento auditável entre o enunciado informal ou canônico (e.g., Fefferman 2000) e a assinatura formal dos tipos em Lean 4, demarcando com clareza o escopo das conclusões e prevenindo que modificações silenciosas de enunciados sejam confundidas com soluções de problemas em aberto.

---

## Consequências

- **Falsos Positivos Eliminados**: Identidades numéricas infinitesimais como $\frac{1}{10^{30}} \neq 0$ são refutadas imediatamente com garantia de integridade.
- **Robustez CLI**: Linha de comando aceita qualquer expressão matemática iniciada por sinal negativo sem falhas de sintaxe.
- **Integridade Científica Auditável**: Suítes de validação não podem ser aprovadas com arquivos residuais ou contagens zeradas.
- **Rigor na Relação AXIOM–Lean**: Fica explicitamente delimitado o papel do verificador formal de tipos em relação à tradução e fidelidade semântica de artigos científicos.
