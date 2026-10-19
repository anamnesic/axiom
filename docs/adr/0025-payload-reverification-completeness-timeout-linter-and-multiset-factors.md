# ADR 0025: Cobertura Completa de Revalidação de Payloads, Controle de Timeout em Provas, Linter Preventivo de Metaprogramação e Checagem Multiconjunto de Fatores

- **Status:** Accepted
- **Data:** 2026-10-19
- **Autores:** Chronokairo AXIOM Core Team & Antigravity Agent

---

## 1. Contexto e Motivação

Durante a formalização do **Dia 07** do plano de verificação matemática (*Iniciação à Aritmética*, Abramo Hefez, Cap. 2.1–2.3: Teorema Fundamental da Aritmética — Unicidade da Decomposição em Fatores Primos), quatro oportunidades de evolução arquitetural no AXIOM foram evidenciadas:

1. **Lacunas na Revalidação de Sessões (`_verify_dict_payload`):** A revalidação automática de sessões de pesquisa (`ResearchSession.revalidate_all()`) tratava apenas `solve`, simplificações elementares, `integrate`, `prove` e `number_theory`. Operações fundamentais como derivadas (`differentiate`), limites (`limit`), equações diferenciais ordinárias (`ode`), álgebra linear (`matrix`), estatística (`statistics`), otimização (`optimize`) e geometria diferencial (`tensor`) falhavam com erro `unsupported result payload kind for re-verification`.
2. **Rigidez de Timeout em Provas Formais:** O tempo de execução do kernel do Lean 4 estava fixado em 30 segundos via variável de ambiente `AXIOM_LEAN_TIMEOUT`, sem suporte a passagem dinâmica de `timeout` por chamada na API Python (`ax.prove`) ou na linha de comando (`--timeout`).
3. **Sobrecarga Oculta de Metaprogramação (`import Lean`):** O prelúdio do Lean 4 já disponibiliza os tipos e teoremas fundamentais da aritmética (`Nat`, `Int`, `List`, `List.Perm`). Ao incluir indevidamente `import Lean` em arquivos puramente matemáticos, o compilador carrega a infraestrutura pesada de elaboração e metaprogramação (macros, parser, compilador), consumindo quase 30 segundos em inicializações a frio no Windows.
4. **Validação Algébrica de Fatoração Multiconjunto:** A unicidade do TFA é definida a menos da ordem dos fatores ($L_1 \sim L_2$). O AXIOM necessitava de uma operação formal e independente em `number_theory` para atestar a equivalência de fatorações primas como multiconjuntos finitos.

---

## 2. Decisões de Arquitetura

### D1: Cobertura Total de Revalidação em `_verify_dict_payload`
- Em `src/axiom/core.py`, expandimos o método `Axiom._verify_dict_payload` para despachar todas as 7 categorias pendentes:
  - `differentiate`: Revalida a ordem da derivada e a variável independente com `self.differentiate`.
  - `limit`: Extrai ponto de aproximação (`--to`) e direção para re-execução via `self.limit`.
  - `ode`: Identifica a função incógnita e a variável independente para validação via `self.ode`.
  - `matrix`: Reconhece operação matricial e vetor/matriz do lado direito via `self.matrix`.
  - `statistics`: Revalida resumos estatísticos com `self.statistics`.
  - `optimize`: Recupera o modo (`minimize`/`maximize`) e restrições com `self.optimize`.
  - `tensor`: Re-executa computações diferenciais e de curvatura com `self.tensor`.

### D2: Controle Dinâmico de Timeout
- Adicionamos o argumento `timeout: int | None = None` nas assinaturas de `LeanEngine.prove()`, `Axiom.prove()` e na CLI `axiom prove --timeout <segundos>`.
- A prioridade é: argumento explícito `timeout` $\to$ variável `AXIOM_LEAN_TIMEOUT` $\to$ default 30s.

### D3: Linter Preventivo de Metaprogramação no LeanEngine
- Implementamos uma verificação pre-flight estática no `LeanEngine.prove()`:
  - Se o código-fonte contém `import Lean` e nenhuma declaração de metaprogramação (`macro`, `syntax`, `elab`, `tactic`, `MetaM`), o motor emite um `PerformanceWarning` estruturado em `Answer.warnings` e `MathResult.warnings`, orientando o uso do prelúdio padrão sem onerar o tempo de compilação.

### D4: Operação `factors_perm_check` em `number_theory`
- Implementamos `ax.number_theory("factors_perm_check", factors1=[...], factors2=[...])` no `SymPyEngine`.
- Implementamos a rotina de verificação independente em `verify_number_theory_op`:
  - Verifica primaridade de todos os elementos.
  - Verifica ordenação canônica e igualdade multiconjunto ($s_1 = s_2$).
  - Valida identidade de produtos multiplicativos ($\prod f_1 = \prod f_2$).
  - Confere garantia `Guarantee.VERIFIED_SUBSTITUTION`.

---

## 3. Consequências e Garantias

- **Integridade Epistêmica Universal:** Qualquer sessão de pesquisa do AXIOM composta por derivações heterogêneas (álgebra, cálculo, estatística, teoria dos números e provas formais) agora pode ser salva em JSON e integralmente revalidada em qualquer nó local sem quebra de garantias.
- **Eficiência e DX:** Provas formais Lean 4 de teoria dos números executam em 2 a 3 segundos, alertando preventivamente contra dependências pesadas desnecessárias.
- **Suíte de Testes:** A suíte unitária de `tests/test_axiom.py` foi expandida para 56 testes (todos aprovados), cobrindo revalidação multiclasse, multiconjuntos de fatores e linting de compilação.
