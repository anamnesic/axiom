# ADR-0016: Integridade de Enunciados Formais, Alinhamento Semântico em 4 Estados e Derivação de Energia Cinética

- **Status**: Aceito (Accepted)
- **Data**: 2026-10-17
- **Versão do AXIOM**: v0.2.5

---

## Contexto

Após a introdução da v0.2.4 (commit `7135938f`), a análise de integridade formal e matemática revelou vulnerabilidades remanescentes no tratamento de especificações formais, no acoplamento de estados de verificação e na derivação de equações físicas:

1. **Vulnerabilidade de Spoofing Léxico e Injeção por Comentários (P0)**:
   A versão anterior utilizava correspondência de palavras-chave sobre o texto bruto do arquivo Lean. Como consequência:
   - Um teorema sobre aritmética elementar como `theorem zeta_add_zero (n : Nat) : n + 0 = n` podia ser associado à Hipótese de Riemann apenas pela substring `zeta`.
   - Comentários no código Lean (como `-- zeta critical line zeros`) podiam injetar palavras-chave e forçar alinhamento indevido.
   - Não havia separação formal entre proposições matemáticas reais e o texto de comentários/nomes de identificadores.

2. **Acoplamento Indevido de Validade de Kernel com Alinhamento Canônico (P1)**:
   O campo `kernel_validity.verified` era forçado a `False` quando um teorema não estava alinhado ao problema canônico aberto. Contudo, a validade do kernel é uma propriedade intrínseca da formalização no assistente de prova (o Lean 4 verificou o teorema sem `sorry` ou axiomas espúrios?). A pertinência em relação a um Problema do Milênio é uma propriedade extrínseca de alinhamento de especificação (`spec_alignment.congruent`). Acoplá-los impedia que o AXIOM atestasse honestamente a validade matemática de lemas gerais em Lean.

3. **Inexistência do Modelo Canônico de 4 Estados de Alinhamento (P1)**:
   A classificação de alinhamento operava de maneira ad-hoc sem um vocabulário formal unificado entre:
   - `verified`: equivalência matemática formal demonstrada e certificada;
   - `scoped`: variante/restrição ontológica reconhecida (ex.: modelo com forçamento externo);
   - `candidate`: associação temática/léxica preliminar sem equivalência formal certificada;
   - `unaligned`: desconexão ontológica ou semântica completa;
   - `tautology_control`: tautologia reflexiva sintática contra afirmação canônica.

4. **Hipóteses Não Declaradas em Provas Canônicas (P1)**:
   Quando premissas adicionais estavam presentes na assinatura formal do teorema mas omitidas na invocação (`declared_hypotheses=[]`), o sistema apenas emitia um aviso (`warning_undeclared_hypotheses`) sem impedir a certificação da prova do problema canônico.

5. **Derivação Manual da Energia Cinética de Taylor–Green (P2)**:
   No relatório de Navier–Stokes, a expressão $E(t) = \pi^2 e^{-4\nu t}$ era assumida a priori em vez de ser calculada passo a passo através da integral dupla da densidade de energia cinética $e(x, y, t) = \frac{1}{2}(u^2 + v^2)$ sobre o domínio $[0, 2\pi]^2$.

---

## Decisões de Arquitetura

### 1. Stripping de Comentários e Extração de Assinaturas Formais

No módulo `src/axiom/core.py`, foram implementadas funções especializadas de pré-processamento de Lean 4:
- `_strip_lean_comments(text: str) -> str`: remove comentários de linha única (`-- ...`) e blocos de comentários aninhados (`/- ... -/`), garantindo que apenas código formal seja analisado.
- `_extract_lean_declarations(clean_source: str) -> list[dict[str, str]]`: extrai cada declaração formal (`theorem`, `lemma`, `def`), capturando o nome do teorema, seus binders (argumentos e tipos) e a proposição matemática estrita declarada após os dois-pontos (`:`).

### 2. Modelo Canônico de Alinhamento Semântico em 4 Estados

A função `_audit_specification_alignment` foi reformulada para operar estritamente sobre as proposições e tipos extraídos:
- **Detecção de Aritmética Elementar**: Teoremas cujas proposições envolvem apenas aritmética reflexiva de `Nat` ou `Int` (ex.: `n + 0 = n`) são categoricamente rejeitados como `unaligned` contra Problemas do Milênio em aberto, mesmo que o nome do identificador contenha termos como `zeta`, `navier` ou `riemann`.
- **4 Estados Canônicos**:
  - `verified`: `is_aligned = True`, `congruent = True` (apenas quando houver prova formal de equivalência semântica e kernel verificado).
  - `scoped`: `is_aligned = True`, `congruent = False` (variantes com hipóteses extras ou forçamento explícito).
  - `candidate`: `is_aligned = True`, `congruent = False` (associação léxica/temática, mas equivalência não certificada).
  - `unaligned`: `is_aligned = False`, `congruent = False` (ontologia incompatível ou aritmética elementar).
  - `tautology_control`: `is_aligned = False`, `congruent = False` (tautologias do tipo `X = X` ou `rfl` contra enunciados canônicos).

### 3. Desacoplamento entre Validade de Kernel e Alinhamento de Especificação

A governança formal do método `Axiom.prove()` agora desacopla categoricamente os três eixos de verificação:
1. `kernel_validity.verified`:
   - Para Lean 4: estritamente `True` se o processo `lean` compilar sem erros, `#print axioms` não reportar `sorry` ou axiomas não confiáveis, e a cobertura do manifesto cobrir os teoremas.
   - Para SymPy: `False` (pois CAS não é assistente de prova interativo de kernel confiável).
2. `spec_alignment`:
   - Avalia a correspondência matemática entre a declaração Lean e o enunciado pretendido.
   - Quando `canonical_statement` for nulo, a auditoria retorna `status: unreviewed` e não bloqueia a prova de lemas auxiliares gerais.
3. `assumptions_audit`:
   - Verifica se todas as hipóteses utilizadas foram explicitamente declaradas.

A garantia final `FORMAL_PROOF` e `verification.passed = True` exige a conjunção de todas as camadas:
```python
is_formal_certified = (
    kernel_passed
    and spec_congruent
    and hypotheses_clean_for_canon
    and not_tautology_for_canon
)
```

### 4. Fail-Closed Estrito para Hipóteses Não Declaradas em Provas Canônicas

Se um teorema é submetido como prova de um problema canônico aberto e a auditoria detecta premissas na assinatura formal não declaradas pelo chamador (`warning_undeclared_hypotheses`), o sistema recusa a certificação com `guarantee = Guarantee.UNVERIFIED` e `verification.passed = False`.

### 5. Derivação Estrita da Energia Cinética de Taylor–Green

No módulo `reports/navier-stokes/validate.py`:
- A densidade de energia cinética $e(x, y, t) = \frac{1}{2}(u^2 + v^2)$ é calculada diretamente do campo de velocidades $\mathbf{u} = (u, v)$.
- A integração espacial sobre $[0, 2\pi] \times [0, 2\pi]$ é realizada simbolicamente de forma sequencial (em $x$ e depois em $y$), resultando matematicamente em $E(t) = \pi^2 e^{-4\nu t}$.
- A taxa de variação temporal $dE/dt = -4\nu\pi^2 e^{-4\nu t}$ é obtida por derivação simbólica direta de $E(t)$.
- O balanço de energia é validado contra a taxa de dissipação viscosa $D(t) = 4\nu\pi^2 e^{-4\nu t}$, derivada integralmente dos gradientes $\nabla \mathbf{u}$.

### 6. Transparência do Modelo Forçado em Lean

O arquivo `examples/navier_stokes_forced.lean` foi documentado explicitamente como um modelo de controle para verificação de metadados contra *specification drift*, e não uma solução analítica da EDP 3D de Navier–Stokes.

---

## Consequências

- **Imunidade contra Spoofing**: O AXIOM não pode ser ludibriado por identificadores com nomes temáticos (`zeta_add_zero`) ou comentários maliciosos para certificar soluções falsas de problemas abertos.
- **Transparência Científica**: Lemas gerais em Lean 4 mantêm sua validade de kernel atestada, enquanto provas de Problemas do Milênio exigem congruência estrita e ausência de hipóteses ocultas.
- **Rigor Físico-Matemático**: A validação de Navier–Stokes não depende de constantes mágicas ou fórmulas injetadas manualmente, derivando energia e dissipação inteiramente dos campos de velocidade.
- **Compatibilidade do Benchmark**: O Millennium Research Bench mantém 100% de taxa fail-closed e 0% de taxa de falsos positivos em todos os 7 problemas.
