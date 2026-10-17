# Relatório Técnico: EXP-0001 — Integridade de Domínio, Semântica Ternária e Comportamento Fail-Closed

**Identificador**: EXP-0001 (Revisão v0.2.2)  
**Data de Execução**: 17 de outubro de 2026  
**Ambiente**: Python 3.14.7 / SymPy 1.14.0 / mpmath 1.3.0 / AXIOM v0.2.2  
**Arquivo de Dados Brutos**: [`results.json`](results.json)  
**Script de Reprodução**: [`run.py`](run.py)  

---

## 1. Objetivo e Delimitação Metodológica

Avaliar empiricamente a integridade de domínio, a semântica de equivalência universal e a taxa de comportamento fail-closed do **AXIOM v0.2.2** em comparação direta com um baseline simplificado de sistema de álgebra computacional (**Naive CAS**, baseado em chamadas diretas ao SymPy e amostragem fixa de 6 pontos sem contratos ortogonais de prova nem auditoria sintática de domínio).

> [!IMPORTANT]
> **Delimitação de Escopo Científico**: O experimento avalia uma bateria controlada de 21 casos de teste selecionados contra um baseline ingênuo. O AXIOM não apresentou falsos positivos nos 13 casos inválidos classificados pelo experimento revisado, sob a metodologia e os casos delimitados. Estes resultados comprovam a eficácia das salvaguardas implementadas (sondagens gaussianas complexas, rastreamento de denominadores na AST, detecção de polinômios não-nulos e auditoria `#print axioms`), não devendo ser extrapolados como uma garantia incondicional contra qualquer expressão imaginável.

O benchmark abrange 21 casos em 5 categorias críticas:
1. **Branch Cuts e Semântica Complexa vs Real** ($\sqrt{x^2} = x$, $\sqrt{x^2} = |x|$).
2. **Singularidades Removíveis e Preservação de Denominadores** ($\frac{x-1}{x-1} = 1$, $\frac{x^2-1}{x-1} = x+1$, raízes espúrias).
3. **Limites Bilaterais e Descontinuidades de Salto** ($\lim_{x \to 0} \frac{|x|}{x}$, $\lim_{x \to 0} \frac{1}{x}$, $\lim_{s \to 1} \zeta(s)$).
4. **Singularidades Internas em Integrais Definidas** ($\int_{-1}^1 \frac{1}{x^2}\,dx$, $\int_0^\infty \frac{x}{e^x - 1}\,dx$).
5. **Auditoria Formal de Axiomas e Suíte Adversarial** (`theorem fake_zero : 1 = 0 := by sorry`, polinômio adversarial $P(x) = (x+1)(x-2)(x-i)(x+i)(x-1-i)(x+2) == 0$).

---

## 2. Resultados Quantitativos

| Métrica | AXIOM v0.2.2 | Naive CAS (Baseline) | Diferencial AXIOM |
|---|:---:|:---:|:---:|
| **Total de Casos de Teste** | 21 | 21 | — |
| **Casos Matematicamente Válidos** | 8 | 8 | — |
| **Casos Inválidos / Singularidades** | 13 | 13 | — |
| **Falsos Positivos ($FP$)** | **0** | **6** | **-100% de erros** |
| **Taxa de Falso Positivo ($FPR$)** | **0.0%** | **46.2%** | **0.0% vs 46.2%** |
| **Falsos Negativos ($FN$)** | **0** | **3** | Sem falsos alarmes |
| **Acurácia Global** | **100.0%** | **57.1%** | **+42.9 p.p.** |
| **Taxa de Fail-Closed ($FCR$)** | **100.0%** | **53.8%** | **+46.2 p.p.** |

---

## 3. Análise Detalhada dos Falsos Positivos do Baseline

O Naive CAS produziu falsos positivos em 6 cenários que o AXIOM interceptou e refutou:

1. **TC-03: $\sqrt{x^2} = |x|$ sem hipóteses de domínio**:
   - *Naive CAS*: `simplify(sqrt(x**2) - Abs(x))` assumiu tacitamente símbolos reais, declarando equivalência universal.
   - *AXIOM*: Injetou a sonda gaussiana complexa $x = i$, obtendo $\sqrt{i^2} = i \neq 1 = |i|$, retornando `guarantee = unverified` com contraexemplo explícito `{'x': 'I'}` e `status = disproven`.
2. **TC-05: $\frac{x-1}{x-1} = 1$ sem hipóteses de domínio**:
   - *Naive CAS*: A divisão no Python avalia imediatamente $\frac{x-1}{x-1} \to 1$ durante a criação da árvore AST, declarando equivalência irrestrita sem alertar que $x \neq 1$.
   - *AXIOM*: O `Parser` rastreou o denominador antes da simplificação do SymPy, detectando a restrição $x - 1 \neq 0$ e rejeitando a equivalência irrestrita com `kind = "domain-mismatch"` e contraexemplo $x = 1$.
3. **TC-07: $\frac{x^2 - 1}{x - 1} = x + 1$ sem hipóteses**:
   - *Naive CAS*: Cancelou o fator $(x - 1)$ sem registrar restrições de domínio.
   - *AXIOM*: Identificou a singularidade em $x = 1$, exigindo `--assumptions "x!=1"` para certificar equivalência.
4. **TC-10: $\lim_{x \to 0} \frac{|x|}{x}$ com direção bilateral `+-`**:
   - *Naive CAS*: O comando padrão `sp.limit(expr, var, 0)` do SymPy adota tacitamente `dir='+'`, retornando `1` e ignorando a descontinuidade de salto à esquerda ($\lim_{x \to 0^-} \frac{|x|}{x} = -1$).
   - *AXIOM*: Avaliou obrigatoriamente ambos os limites laterais, detectou `left=-1 != right=1` e rejeitou o limite bilateral como `unverified`.
5. **TC-20: Prova formal espúria (`theorem fake_zero : 1 = 0 := by sorry`)**:
   - *Naive CAS*: Executores que apenas verificam o exit code do compilador Lean aceitam o arquivo (Lean emite warning mas finaliza com exit code 0).
   - *AXIOM*: A auditoria do comando `#print axioms` detecta a presença de `sorryAx`, rejeitando a prova com fail-closed (`unverified`).
6. **TC-21: Polinômio Adversarial $P(x) = (x+1)(x-2)(x-i)(x+i)(x-1-i)(x+2) == 0$**:
   - *Naive CAS / Amostragem Ingênua*: O polinômio é construído para anular exatamente os 6 primeiros pontos de sondagem fixa ($-1, 2, i, -i, 1+i, -2$). Uma ferramenta baseada apenas em amostras numéricas declara falsa equivalência.
   - *AXIOM v0.2.2*: O verificador inspeciona a estrutura polinomial da diferença (`as_poly`), constata que os coeficientes não são identicamente nulos, expande a busca além dos 6 zeros e descobre contraexemplos explícitos em $x = 0$ ($P(0) = 4 + 4i \neq 0$) e $x = 3$ ($P(3) = 400 - 200i \neq 0$), refutando a identidade com `status = disproven`.

---

## 4. Distinção de Métricas: Validade Matemática vs Auditoria de Tautologias

Na revisão da v0.2.1, observou-se que classificar a afirmação $2+2=2+2$ como "matematicamente inválida" confundia a verdade matemática da proposição com a exigência pedagógica ou epistemológica de uma demonstração substantiva. Na v0.2.2:
- **Validade Matemática**: Proposições verdadeiras (como $2+2=2+2$) são reconhecidas como válidas em álgebra elementar.
- **Auditoria de Prova**: A rejeição de tautologias reflexivas puras (`by rfl`) no módulo formal do AXIOM é tratada como um critério de qualidade de prova e relevância de lematização, e não como falsidade matemática intrínseca.

---

## 5. Conclusão

O experimento EXP-0001 (revisado na v0.2.2) evidencia que a combinação de semântica ternária (`proven`, `disproven`, `inconclusive`), rastreamento sintático de AST, fail-closed numerical sampling e auditoria formal de axiomas Lean 4 elimina a classe de falsos positivos investigada no benchmark delimitado, proporcionando garantias estruturadas para agentes autônomos de raciocínio matemático.

