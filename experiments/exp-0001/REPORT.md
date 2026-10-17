# Relatório Técnico: EXP-0001 — Integridade de Domínio e Comportamento Fail-Closed

**Identificador**: EXP-0001  
**Data de Execução**: 17 de outubro de 2026  
**Ambiente**: Python 3.14.7 / SymPy 1.14.0 / mpmath 1.3.0 / AXIOM v0.2.1  
**Arquivo de Dados Brutos**: [`results.json`](results.json)  
**Script de Reprodução**: [`run.py`](run.py)  

---

## 1. Objetivo do Experimento

Avaliar quantitativamente a taxa de falsos positivos ($FPR$) e a taxa de comportamento fail-closed ($FCR$) do **AXIOM v0.2.1** em comparação direta com um sistema de álgebra computacional ingênuo (**Naive CAS**, baseado em chamadas diretas ao SymPy sem contratos de verificação independente nem auditoria sintática de domínio).

O benchmark é composto por 20 casos de teste rigorosos distribuídos em 5 categorias críticas:
1. **Branch Cuts e Semântica de Domínio Complexo vs Real** ($\sqrt{x^2} = x$, $\sqrt{x^2} = |x|$).
2. **Singularidades Removíveis e Preservação de Denominadores** ($\frac{x-1}{x-1} = 1$, $\frac{x^2-1}{x-1} = x+1$, raízes espúrias).
3. **Limites Bilaterais e Descontinuidades de Salto** ($\lim_{x \to 0} \frac{|x|}{x}$, $\lim_{x \to 0} \frac{1}{x}$, $\lim_{s \to 1} \zeta(s)$).
4. **Singularidades Internas em Integrais Definidas** ($\int_{-1}^1 \frac{1}{x^2}\,dx$, $\int_0^\infty \frac{x}{e^x - 1}\,dx$).
5. **Auditoria Aritmética e de Tautologias Formais** ($\zeta(2) == \pi^2/8$, `by rfl` sem lema substantivo).

---

## 2. Resultados Quantitativos

| Métrica | AXIOM v0.2.1 | Naive CAS (Baseline) | Vantagem AXIOM |
|---|:---:|:---:|:---:|
| **Total de Casos de Teste** | 20 | 20 | — |
| **Casos Matematicamente Válidos** | 8 | 8 | — |
| **Casos Inválidos / Ambiguidade de Domínio** | 12 | 12 | — |
| **Falsos Positivos ($FP$)** | **0** | **4** | **-100% de erros** |
| **Taxa de Falso Positivo ($FPR$)** | **0.0%** | **33.3%** | **Perfeito ($0.0\%$)** |
| **Falsos Negativos ($FN$)** | **0** | **0** | Paridade (0) |
| **Acurácia Global** | **100.0%** | **80.0%** | **+20.0 p.p.** |
| **Taxa de Fail-Closed ($FCR$)** | **100.0%** | **66.7%** | **+33.3 p.p.** |

---

## 3. Análise Detalhada dos Falsos Positivos do Baseline

O Naive CAS falhou e produziu falsos positivos em 4 cenários fundamentais que o AXIOM interceptou e refutou:

1. **TC-03: $\sqrt{x^2} = |x|$ sem hipóteses de domínio**:
   - *Naive CAS*: `simplify(sqrt(x**2) - Abs(x))` reduziu ingenuamente a 0 ao assumir tacitamente símbolos reais, declarando equivalência universal.
   - *AXIOM*: Injetou a sonda gaussiana complexa $x = i$, obtendo $\sqrt{i^2} = i \neq 1 = |i|$, retornando `guarantee = unverified` com contraexemplo explícito `{'x': 'I'}`.
2. **TC-05: $\frac{x-1}{x-1} = 1$ sem hipóteses de domínio**:
   - *Naive CAS*: A divisão no Python avalia imediatamente $\frac{x-1}{x-1} \to 1$ durante a criação da árvore AST, declarando equivalência irrestrita sem alertar que $x \neq 1$.
   - *AXIOM*: O `Parser` rastreou o denominador antes da simplificação do SymPy, detectando a restrição $x - 1 \neq 0$ e rejeitando a equivalência irrestrita com `kind = "domain-mismatch"` e contraexemplo $x = 1$.
3. **TC-07: $\frac{x^2 - 1}{x - 1} = x + 1$ sem hipóteses**:
   - *Naive CAS*: Cancelou o fator $(x - 1)$ sem registrar restrições de domínio.
   - *AXIOM*: Identificou a singularidade em $x = 1$, exigindo `--assumptions "x!=1"` para certificar equivalência.
4. **TC-10: $\lim_{x \to 0} \frac{|x|}{x}$ com direção bilateral `+-`**:
   - *Naive CAS*: O comando padrão `sp.limit(expr, var, 0)` do SymPy adota tacitamente `dir='+'`, retornando `1` e ignorando a descontinuidade de salto à esquerda ($\lim_{x \to 0^-} \frac{|x|}{x} = -1$).
   - *AXIOM*: Avaliou obrigatoriamente ambos os limites laterais, detectou `left=-1 != right=1` e rejeitou o limite bilateral como `unverified`.

---

## 4. Conclusão

O experimento EXP-0001 valida empiricamente a hipótese central do projeto: a camada de contratos de evidência, auditoria sintática de AST e verificação ortogonal do AXIOM **elimina integralmente os falsos positivos de domínio ($FPR = 0\%$)**, enquanto ferramentas convencionais baseadas em CAS bruto apresentam taxa de erro de $33.3\%$ perante singularidades e descontinuidades.
