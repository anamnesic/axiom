# Metodologia Científica e Protocolos de Validação — AXIOM

Este documento estabelece a metodologia de validação formal, verificação empírica e critérios de garantia matemática do **Chronokairo AXIOM**. O rigor do sistema repousa no princípio de que **nenhuma operação matemática é aceita sem verificação independente ortogonal e registro explícito de evidências**.

---

## 1. Princípios Metodológicos Fundamentais

1. **Separação entre Descoberta e Verificação**: O componente que descobre ou calcula uma resposta (CAS ou LLM) nunca é o único responsável por sua validação. A resposta é sempre submetida a um segundo método matematicamente independente.
2. **Comportamento Estritamente Fail-Closed**: Perante ambiguidade, ausência de hipóteses de domínio, singularidades internas ou inconclusão numérica, o sistema rejeita a elevação de garantia, retornando `guarantee = unverified` e documentando as limitações observadas.
3. **Integridade de Domínio e Hipóteses Explícitas**: Nenhuma identidade condicional (e.g. $\sqrt{x^2} = x$ ou $\frac{x}{x} = 1$) pode ser declarada verdadeira sem a especificação prévia das hipóteses de domínio (e.g. $x > 0$ ou $x \neq 0$).
4. **Reprodutibilidade Determinística Total**: Toda chamada bem-sucedida deve registrar comandos e parâmetros exatos (`reproducible_with`), hashes de código e versões dos motores para auditoria externa.

---

## 2. A Hierarquia de Garantias Matemáticas (`Guarantee`)

O AXIOM adota uma ordenação parcial estrita de garantias epistemológicas, onde cada nível impõe critérios formais mais rígidos:

```
[FORMAL_PROOF]                (Nível 6 — Certificação por Kernel de Tipos Dependentes Lean 4)
      ▲
[EXACT_SYMBOLIC]              (Nível 5 — Identidade Simbólica Fechada com Diferença Nula)
      ▲
[VERIFIED_SUBSTITUTION]       (Nível 4 — Raiz Exata Conferida no Domínio da Equação Original)
      ▲
[NUMERICAL_APPROXIMATION]     (Nível 3 — Limite/Integral/Avaliação com Tolerância ε e Erro Delimitado)
      ▲
[HEURISTIC]                   (Nível 2 — Simplificação sem Verificação Completa ou Busca Estocástica)
      ▲
[UNVERIFIED]                  (Nível 1 — Inconclusivo, Refutado, Divergente ou Violação de Domínio)
```

Garantias operacionais específicas não concorrem com as alegações matemáticas:
- `STRUCTURAL_PARSE`: Representação canônica da árvore sintática validada por round-trip determinístico.
- `CATALOG_LOOKUP`: Localização de assinatura ou lema em biblioteca matemática auditada (Mathlib4).
- `SAMPLED_VISUALIZATION`: Amostragem de pontos finitos para renderização gráfica de apoio visual.

---

## 3. Protocolos de Verificação por Domínio Matemático

### 3.1. Equivalência Algébrica e Integridade de Domínio
- **Procedimento**:
  1. O `Parser` captura todos os denominadores sintáticos e raízes pares antes de permitir que o SymPy simplifique a expressão.
  2. Determina-se o conjunto de restrições de domínio ($D_{\text{lhs}}$ e $D_{\text{rhs}}$) e pontos singulares excluídos.
  3. Se $D_{\text{lhs}} \neq D_{\text{rhs}}$ e nenhuma hipótese externa (`--assumptions`) descarta a singularidade, a equivalência irrestrita é refutada (`kind = "domain-mismatch"`, `guarantee = unverified`).
  4. Para símbolos não restritos em $\mathbb{C}$, injetam-se amostras gaussianas complexas ($i, -i, 1+i$) para detectar branch cuts.
  5. Se a diferença simbólica reduz a 0 e todas as amostras numéricas concordam sem violação de domínio, a garantia é elevada para `exact-symbolic`.

### 3.2. Solução de Equações e Sistemas
- **Procedimento**:
  1. As raízes candidatas são geradas pelo motor algébrico.
  2. Cada raiz candidata $r_i$ é substituída diretamente na equação original $f(r_i) = 0$.
  3. O verificador checa se $r_i$ pertence ao domínio da equação (descartando polos $0/0$ ou logaritmos de números não-positivos).
  4. Avalia-se o campo `solution_complete`: para polinômios, o Teorema Fundamental da Álgebra garante completude; para equações transcendentes (e.g. $\sin(x) = 0$), reporta-se `solution_complete = false` acompanhado da família periódica (`ImageSet`).

### 3.3. Cálculo Diferencial
- **Procedimento**:
  1. A derivada simbólica candidata $f'(x)$ é calculada.
  2. O verificador calcula diferenças finitas centrais de alta precisão via `mpmath`:
     $$f'(x_0) \approx \frac{f(x_0 + h) - f(x_0 - h)}{2h}$$
     com $h = 10^{-6}$ e aritmética de 35 dígitos decimais em múltiplos pontos de amostragem.
  3. Testa-se o round-trip de antiderivação simbólica $\int f'(x)\,dx - f(x) = C$. Havendo concordância simbólica e numérica, garante-se `exact-symbolic`.

### 3.4. Cálculo Integral
- **Procedimento**:
  1. **Integrais Indefinidas**: O resultado $F(x)$ é derivado simbolicamente; verifica-se se $F'(x) - f(x) = 0$.
  2. **Integrais Definidas**:
     - Busca ativa de polos internos: o verificador investiga se existem singularidades reais de $f(x)$ no interior do intervalo aberto $(a, b)$. Se existirem polos não-integráveis, a aplicação ingênua do TFC é barrada (`kind = "interior-singularity-check"`, `guarantee = unverified`).
     - Conferência por quadratura adaptativa de Gauss-Legendre (`mpmath.quad`) com estimativa rigorosa de erro residual.
     - Havendo convergência de quadratura e confirmação analítica, garante-se `exact-symbolic` ou `numerical-approximation`.

### 3.5. Limites
- **Procedimento**:
  1. Para limites bilaterais (`direction = "+-"`), o motor calcula explicitamente o limite à esquerda ($L_-$) e o limite à direita ($L_+$).
  2. Se $L_- \neq L_+$, ou se um dos lados divergir para $\pm\infty$ com sinais opostos, o limite bilateral é declarado inexistente (`guarantee = unverified`).
  3. Valores infinitos não-assinados no plano complexo (`zoo`) são rejeitados para limites reais.
  4. Amostragem sequencial de aproximação geométrica ($x_k = x_0 \pm 10^{-k}$) confirma a estabilidade numérica.

### 3.6. Demonstração Formal em Lean 4
- **Procedimento**:
  1. O arquivo ou código é submetido ao compilador do Lean 4 via ambiente Lake (`lake env lean`).
  2. O comando `#print axioms <decl>` é injetado e executado obrigatoriamente para cada lema ou teorema.
  3. Se a prova contiver `sorry`, `admit` ou `sorryAx`, é classificada como incompleta (`guarantee = unverified`).
  4. Se depender de axiomas de usuário não certificados, é rejeitada.
  5. Se for uma mera igualdade reflexiva sintática provada por `rfl` sem lema substantivo, o AXIOM identifica a tautologia e exige declarações com conteúdo matemático.
  6. Passando por todos os critérios, recebe a garantia máxima: `formal-proof`.

---

## 4. Critérios de Aceite para Experimentos Quantitativos

Em qualquer experimento ou benchmark comparativo do AXIOM:
1. **Taxa de Falsos Positivos ($FP$)**: Deve ser **rigorosamente zero** ($FP = 0$). Nenhuma falsidade matemática ou violação de domínio pode receber garantia de comprovação.
2. **Taxa de Fail-Closed ($FC$)**: Diante de singularidades, branch cuts sem hipóteses ou limites inexistentes, a taxa de rejeição deve ser de 100%.
3. **Determinismo**: 100% dos resultados devem ser idênticos entre execuções repetidas com os mesmos parâmetros.
