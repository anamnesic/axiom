# Log de Estudos e Demonstrações Matemáticas — AXIOM

Este registro documenta as sessões de estudo, resolução de exercícios analíticos e demonstrações formais conduzidas no programa de pesquisa do Chronokairo AXIOM. Todas as derivações contam com conferência cruzada entre computação simbólica (CAS), verificação numérica independente de alta precisão e certificação formal de teoremas (Lean 4).

---

## Sessão 01 — Fundamentos e Álgebra Elementar
- **Data**: 2026-09-20
- **Disciplina**: Fundações e Pré-Cálculo
- **Bibliografia**: Iezzi, *FME Vol. 1*; Axler, *Precalculus*.

### Tópicos Abordados
- Propriedades de corpo de $\mathbb{R}$, valor absoluto e desigualdade triangular: $|a + b| \le |a| + |b|$.
- Domínio de funções algébricas racionais e radicais pares.

### Exercícios Selecionados e Resoluções
1. **Exercício**: Determinar o conjunto solução e domínio da equação racional $\frac{x^2 - 1}{x - 1} = 2$.
   - *Resolução Analítica*: Para $x \neq 1$, $\frac{(x - 1)(x + 1)}{x - 1} = x + 1 = 2 \implies x = 1$. Porém, $x = 1$ viola a restrição de domínio do denominador original. Logo, o conjunto solução é vazio: $S = \emptyset$.
   - *Verificação AXIOM*:
     ```powershell
     axiom solve "(x^2 - 1)/(x - 1) = 2"
     # Resultado: ok: true, value: [], guarantee: verified-substitution
     axiom verify "(x^2 - 1)/(x - 1) = 2" --solutions 1
     # Resultado: ok: true, guarantee: unverified, kind: substitution-domain-error (FAILED)
     ```
2. **Exercício**: Verificar a identidade $\sqrt{x^2} = x$ versus $\sqrt{x^2} = |x|$.
   - *Análise*: No domínio complexo $\mathbb{C}$, $\sqrt{x^2} \neq |x|$ (contraexemplo $x = i$). No domínio real $\mathbb{R}$, $\sqrt{x^2} = |x|$ é universal. Para $x > 0$, $\sqrt{x^2} = x$.
   - *Verificação AXIOM*:
     ```powershell
     axiom compare "sqrt(x^2)" "x"
     # Refutado com contraexemplo x = -1 (unverified)
     axiom compare "sqrt(x^2)" "x" -A "x:positive"
     # Aprovado: exact-symbolic
     axiom compare "sqrt(x^2)" "Abs(x)"
     # Refutado no domínio complexo com contraexemplo x = I (unverified)
     axiom compare "sqrt(x^2)" "Abs(x)" -A "x:real"
     # Aprovado: exact-symbolic
     ```

---

## Sessão 02 — Cálculo Diferencial e Integral
- **Data**: 2026-09-28
- **Disciplina**: Cálculo 1 e 2
- **Bibliografia**: Guidorizzi, *Um Curso de Cálculo* (Vols. 1 e 2); Apostol, *Calculus I*.

### Tópicos Abordados
- Teorema Fundamental do Cálculo (TFC): $\frac{d}{dx} \int_a^x f(t)\,dt = f(x)$.
- Limites fundamentais e regra de L'Hôpital.
- Limites laterais em descontinuidades essenciais e de salto.

### Demonstração: O Limite Fundamental $\lim_{x \to 0} \frac{\sin(x)}{x} = 1$
- *Demonstração Geométrica*: Pelo círculo trigonométrico unitário, para $0 < x < \pi/2$:
  $$\sin(x) < x < \tan(x) \implies 1 < \frac{x}{\sin(x)} < \frac{1}{\cos(x)} \implies \cos(x) < \frac{\sin(x)}{x} < 1$$
  Como $\lim_{x \to 0^+} \cos(x) = 1$, pelo Teorema do Confronto (Sandwich), $\lim_{x \to 0^+} \frac{\sin(x)}{x} = 1$. Por paridade ($\sin(-x)/(-x) = \sin(x)/x$), o limite à esquerda coincide. Logo, o limite bilateral existe e vale 1.
- *Conferência AXIOM*:
  ```powershell
  axiom limit "sin(x)/x" --variable x --to 0 --dir +-
  # Resultado: value: 1, guarantee: exact-symbolic, verification: passed
  ```

### Exercício de Auditoria: Singularidades e Limites Bilaterais
- **Exercício**: Analisar a existência de $\lim_{x \to 0} \frac{|x|}{x}$ e $\lim_{x \to 0} \frac{1}{x}$.
  - *Análise*: $\lim_{x \to 0^+} \frac{|x|}{x} = +1$, $\lim_{x \to 0^-} \frac{|x|}{x} = -1$. Como $+1 \neq -1$, o limite bilateral não existe. Para $1/x$, limites laterais divergem para $+\infty$ e $-\infty$.
  - *Verificação AXIOM*:
    ```powershell
    axiom limit "Abs(x)/x" --variable x --to 0 --dir +-
    # Resultado: guarantee: unverified, left=-1, right=1 (mismatch)
    axiom limit "1/x" --variable x --to 0 --dir +-
    # Resultado: guarantee: unverified, left=-oo, right=oo (mismatch)
    ```

---

## Sessão 03 — Álgebra Linear e Teoria Espectral
- **Data**: 2026-10-05
- **Disciplina**: Álgebra Linear
- **Bibliografia**: Lima, *Álgebra Linear*; Axler, *Linear Algebra Done Right*.

### Tópicos Abordados
- Autovalores e autovetores de matrizes simétricas reais.
- Diagonalização e invariância do traço e determinante.

### Exercício Resolvido
- **Exercício**: Dada a matriz $A = \begin{pmatrix} 2 & 1 \\ 1 & 2 \end{pmatrix}$, determinar autovalores, autovetores e verificar os invariantes espectrais.
  - *Resolução*:
    Polinômio característico: $\det(A - \lambda I) = (2 - \lambda)^2 - 1 = \lambda^2 - 4\lambda + 3 = (\lambda - 1)(\lambda - 3) = 0$.
    Autovalores: $\lambda_1 = 1$, $\lambda_2 = 3$.
    Autovetores: para $\lambda = 1$, $v_1 = (-1, 1)^T$; para $\lambda = 3$, $v_2 = (1, 1)^T$.
    Invariantes: $\text{tr}(A) = 2 + 2 = 4 = 1 + 3$; $\det(A) = 4 - 1 = 3 = 1 \cdot 3$.
  - *Verificação AXIOM*:
    ```powershell
    axiom matrix "[[2, 1], [1, 2]]" --op eigen
    # Resultado: eigenvalues: [1, 3], trace: 4, det: 3, guarantee: verified-substitution
    ```

---

## Sessão 04 — Equações Diferenciais e Geometria Diferencial
- **Data**: 2026-10-12
- **Disciplina**: EDO e Geometria Diferencial
- **Bibliografia**: Boyce & DiPrima, *EDO*; do Carmo, *Geometria Diferencial de Curvas e Superfícies*.

### Tópicos Abordados
- Símbolos de Christoffel da métrica polar plana: $ds^2 = dr^2 + r^2 d\theta^2$.
- Solução e verificação de EDO de 2ª ordem com oscilador harmônico amortecido.

### Demonstração: Curvatura Plana da Métrica Polar
- *Métrica*: $g_{rr} = 1$, $g_{\theta\theta} = r^2$, $g_{r\theta} = 0$.
- *Símbolos de Christoffel não-nulos*:
  $$\Gamma^r_{\theta\theta} = -\frac{1}{2} g^{rr} \frac{\partial g_{\theta\theta}}{\partial r} = -r, \quad \Gamma^\theta_{r\theta} = \Gamma^\theta_{\theta r} = \frac{1}{r}$$
- *Curvatura*: Tensor de Riemann nulo $R^\rho_{\sigma\mu\nu} = 0$, escalar de Ricci $R = 0$ (o plano é intrinsecamente plano).
- *Verificação AXIOM*:
  ```powershell
  axiom tensor "polar"
  # Símbolos não nulos: Gamma^r_{theta,theta} = -r, Gamma^theta_{r,theta} = 1/r
  # Escalar de Ricci: 0, guarantee: verified-substitution
  ```

---

## Sessão 05 — Teoria Analítica dos Números e a Função Zeta de Riemann
- **Data**: 2026-10-17
- **Disciplina**: Análise Complexa e Teoria dos Números
- **Bibliografia**: Bombieri, *The Riemann Hypothesis* (Clay Math); Stein & Shakarchi, *Complex Analysis*.

### Demonstração: Integral de Mellin para $\zeta(2) = \frac{\pi^2}{6}$
- *Demonstração*:
  Consideremos a representação da função zeta via integral de Bose-Einstein:
  $$\zeta(s) \Gamma(s) = \int_0^\infty \frac{x^{s-1}}{e^x - 1}\,dx$$
  Para $s = 2$, temos $\Gamma(2) = 1! = 1$, logo:
  $$\zeta(2) = \int_0^\infty \frac{x}{e^x - 1}\,dx$$
  Aplicando a substituição $u = e^{-x} \iff x = -\ln(u)$, $dx = -\frac{du}{u}$:
  Quando $x \to 0$, $u \to 1$; quando $x \to \infty$, $u \to 0$.
  $$\int_0^\infty \frac{x}{e^x - 1}\,dx = \int_0^1 \frac{-\ln(u)}{\frac{1}{u} - 1} \frac{du}{u} = \int_0^1 \frac{\ln(u)}{u - 1}\,du$$
  Expandindo $\frac{1}{1 - u} = \sum_{k=0}^\infty u^k$ para $u \in (0, 1)$:
  $$-\int_0^1 \ln(u) \sum_{k=0}^\infty u^k\,du = -\sum_{k=0}^\infty \left[ \frac{u^{k+1} \ln(u)}{k+1} - \frac{u^{k+1}}{(k+1)^2} \right]_0^1 = \sum_{k=0}^\infty \frac{1}{(k+1)^2} = \sum_{n=1}^\infty \frac{n^{-2}} = \frac{\pi^2}{6}$$
- *Conferência AXIOM*:
  ```powershell
  axiom evaluate "zeta(2)"
  # Resultado: pi**2/6 (exact-symbolic)
  axiom compare "zeta(2)" "pi^2/6"
  # Resultado: equivalent (exact-symbolic)
  ```

---

## Sessão 06 — Prova Formal no Lean 4
- **Data**: 2026-10-17
- **Disciplina**: Lógica Matemática e Métodos Formais
- **Bibliografia**: Avigad, de Moura & Kong, *Theorem Proving in Lean 4*.

### Teorema Formalizado: Reflexividade e Auditoria de Axiomas
- *Código Lean 4*:
  ```lean
  theorem add_zero_nat (n : Nat) : n + 0 = n := by
    rfl
  ```
- *Auditoria AXIOM*:
  O kernel do Lean 4 typecheckou a prova. O auditor do AXIOM executou `#print axioms add_zero_nat`, confirmando que nenhuma hipótese externa (`sorry`, axiomas arbitrários de usuário) foi utilizada, e registrou os axiomas constitutivos.
