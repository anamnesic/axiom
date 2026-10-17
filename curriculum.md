# Curriculum Matemático — Programa de Pesquisa AXIOM

Este documento sistematiza a base matemática fundamental, a bibliografia canônica e a progressão conceitual do programa de pesquisa do **Chronokairo AXIOM (Mathematical Reasoning Engine)**. O currículo estrutura os domínios matemáticos integrados aos motores simbólicos, verificadores independentes e provadores formais da arquitetura.

---

## 1. Fundações e Pré-Cálculo

### Ementa
Teoria elementar dos conjuntos, lógica proposicional básica, axiomas de Peano e dos números reais ($\mathbb{R}$ como corpo ordenado completo), desigualdades fundamentais, trigonometria analítica, relações e funções (injetividade, sobrejetividade, bijeção, inversa e composição).

### Bibliografia Canônica
- **Axler, S.** *Precalculus: A Prelude to Calculus*. Wiley.
- **Iezzi, G. et al.** *Fundamentos da Matemática Elementar* (Vols. 1, 2, 3: Conjuntos, Funções, Trigonometria). Atual Editora.
- **Barbosa, J. L. M.** *Geometria Euclidiana Plana*. Coleção do Professor de Matemática, SBM.
- **Lima, E. L.** *Números e Funções Reais*. Coleção PROFMAT, SBM.

### Conexão com o AXIOM
- `axiom parse`: análise sintática de expressões, precedência de operadores e desambiguação relacional.
- `axiom compare`: preservação estrita de restrições de domínio ($x \neq 0$, radicandos não-negativos) e auditoria de hipóteses (`--assumptions`).

---

## 2. Cálculo Diferencial e Integral (1 a 4)

### Ementa
- **Uma Variável**: Limites ($\varepsilon$-$\delta$), continuidade, derivadas, teoremas fundamentais (Rolle, TVM, L'Hôpital), Teorema Fundamental do Cálculo, técnicas de integração, integrais impróprias, sequências e séries infinitas (convergência, séries de Taylor/Maclaurin).
- **Múltiplas Variáveis e Vetorial**: Funções de várias variáveis, derivadas parciais, gradiente, matriz Hessiana, multiplicadores de Lagrange, integrais duplas e triplas, campos vetoriais, integrais de linha e superfície, Teoremas de Green, Stokes e Gauss (Divergência).

### Bibliografia Canônica
- **Guidorizzi, H. L.** *Um Curso de Cálculo* (Volumes 1 a 4, 6ª edição). LTC.
- **Apostol, T. M.** *Calculus* (Volumes 1 e 2). John Wiley & Sons.
- **Spivak, M.** *Calculus*. Publish or Perish.
- **Stewart, J.** *Calculus: Early Transcendentals*. Cengage Learning.

### Conexão com o AXIOM
- `axiom differentiate`: derivação simbólica com conferência numérica via diferenças finitas de alta precisão.
- `axiom integrate`: integração simbólica com conferência dupla por diferenciação da antiderivada (TFC) e quadratura adaptativa de Gauss-Legendre. Detecção fail-closed de polos internos (`verify_integral`).
- `axiom limit`: limites direcionais e bilaterais explícitos, rejeição de descontinuidades de salto e polos assimétricos.

---

## 3. Equações Diferenciais Ordinárias (EDO) e Sistemas Dinâmicos

### Ementa
Equações lineares de 1ª ordem, equações separáveis e exatas, fatores integrantes, EDOs lineares de ordem superior com coeficientes constantes, variação de parâmetros, transformadas de Laplace e convolução, sistemas lineares de EDOs, plano de fase e estabilidade linear.

### Bibliografia Canônica
- **Boyce, W. E., DiPrima, R. C.** *Elementary Differential Equations and Boundary Value Problems*. Wiley.
- **Figueiredo, D. G., Neves, A. F.** *Equações Diferenciais Aplicadas*. Coleção Matemática Universitária, IMPA.
- **Sotomayor, J.** *Lições de Equações Diferenciais Ordinárias*. Projeto Euclides, IMPA.
- **Strang, G.** *Differential Equations and Linear Algebra*. Wellesley-Cambridge Press.

### Conexão com o AXIOM
- `axiom ode`: resolução de equações diferenciais lineares e exatas com verificação independente obrigatória por substituição da função candidata na equação diferencial original.

---

## 4. Álgebra Linear e Álgebra Multilinear

### Ementa
Espaços e subespaços vetoriais sobre corpos arbitrários ($\mathbb{R}, \mathbb{C}, \mathbb{F}_p$), transformações lineares, núcleo e imagem, teorema do posto-nulidade, matrizes e determinantes, autovalores, autovetores e polinômio característico, diagonalização, espaços com produto interno, operadores adjuntos, Teorema Espectral, decomposição em valores singulares (SVD), formas canônicas de Jordan, tensores e produtos tensoriais.

### Bibliografia Canônica
- **Lima, E. L.** *Álgebra Linear*. Coleção Matemática Universitária, IMPA.
- **Axler, S.** *Linear Algebra Done Right* (4ª edição). Springer.
- **Hoffman, K., Kunze, R.** *Linear Algebra* (2ª edição). Prentice-Hall.
- **Strang, G.** *Introduction to Linear Algebra*. Wellesley-Cambridge Press.

### Conexão com o AXIOM
- `axiom matrix`: computação de determinantes, traços, formas escalonadas reduzidas (RREF), decomposição LU e autovalores/autovetores com verificação de invariantes de similaridade.
- `axiom tensor`: cálculo tensorial, símbolos de Christoffel e tensores de curvatura de Riemann/Ricci.

---

## 5. Álgebra Abstrata

### Ementa
- **Grupos**: Grupos cíclicos, classes laterais, Teorema de Lagrange, subgrupos normais e grupos quociente, homomorfismos e Teoremas de Isomorfismo, ações de grupo, Teoremas de Sylow.
- **Anéis e Corpos**: Anéis comutativos, ideais e anéis quociente, domínios de integridade, anéis euclidianos, fatoração única (DIP, DFU), polinômios irredutíveis, extensões de corpos e introdução à Teoria de Galois.

### Bibliografia Canônica
- **Hefez, A.** *Curso de Álgebra* (Volumes 1 e 2). Coleção Matemática Universitária, IMPA.
- **Gallian, J. A.** *Contemporary Abstract Algebra* (8ª edição). Cengage Learning.
- **Herstein, I. N.** *Topics in Algebra*. John Wiley & Sons.
- **Lang, S.** *Algebra* (Graduate Texts in Mathematics). Springer.

### Conexão com o AXIOM
- `axiom prove`: formalização de lemas de teoria de grupos e anéis no kernel do Lean 4.
- `axiom number-theory`: aritméica modular, Teorema Chinês dos Restos e anéis $\mathbb{Z}/n\mathbb{Z}$.

---

## 6. Análise Real

### Ementa
Topologia da reta e de $\mathbb{R}^n$ (conjuntos abertos, fechados, compactos e conexos), sequências e séries de números reais, limites superiores e inferiores, continuidade uniforme, Teorema de Heine-Borel, diferenciabilidade em $\mathbb{R}^n$, Teoremas da Função Inversa e da Função Implícita, integração de Riemann-Darboux.

### Bibliografia Canônica
- **Lima, E. L.** *Curso de Análise* (Volumes 1 e 2). Projeto Euclides, IMPA.
- **Ávila, G.** *Introdução à Análise Matemática*. Edgard Blücher.
- **Rudin, W.** *Principles of Mathematical Analysis* (3ª edição). McGraw-Hill.
- **Tao, T.** *Analysis I & II* (Texts and Readings in Mathematics). Hindustan Book Agency / Springer.

### Conexão com o AXIOM
- Verificação de limites, continuidade de integrais paramétricas e auditoria de branch cuts complexos versus reais.

---

## 7. Análise Complexa

### Ementa
Números complexos e geometria no plano complexo, funções holomorfas e equações de Cauchy-Riemann, funções analíticas e séries de potências, integração no plano complexo e Teorema de Cauchy-Goursat, Fórmula Integral de Cauchy e consequências (Liouville, Teorema Fundamental da Álgebra), séries de Laurent e singularidades isoladas (removíveis, polos e essenciais), Teorema dos Resíduos e cálculo de integrais reais, princípio do argumento e Teorema de Rouché, continuação analítica e função zeta de Riemann.

### Bibliografia Canônica
- **Soares, M. G.** *Cálculo em uma Variável Complexa*. Coleção Matemática Universitária, IMPA.
- **Brown, J. W., Churchill, R. V.** *Complex Variables and Applications* (8ª edição). McGraw-Hill.
- **Stein, E. M., Shakarchi, R.** *Complex Analysis* (Princeton Lectures in Analysis, Vol. 2). Princeton University Press.
- **Ahlfors, L. V.** *Complex Analysis*. McGraw-Hill.

### Conexão com o AXIOM
- `axiom limit` e `axiom evaluate`: cálculo de polos, resíduos e valores especiais de funções transcendentais (e.g. $\zeta(s)$, $\Gamma(s)$).
- Provas de consistência da linha crítica de Riemann $\text{Re}(s) = 1/2$.

---

## 8. Geometria Diferencial

### Ementa
Curvas no espaço euclidiano (curvatura, torção, triedro de Frenet-Serret), superfícies regulares em $\mathbb{R}^3$, plano tangente e primeira forma fundamental, aplicação de Gauss e segunda forma fundamental, curvatura de Gauss e curvatura média, Teorema Egregium de Gauss, geodésicas e Teorema de Gauss-Bonnet, variedades diferenciáveis e métricas pseudo-riemannianas da relatividade geral.

### Bibliografia Canônica
- **do Carmo, M. P.** *Geometria Diferencial de Curvas e Superfícies*. Coleção Textos Universitários, SBM.
- **Tenenblat, K.** *Introdução à Geometria Diferencial*. Edgard Blücher.
- **do Carmo, M. P.** *Riemannian Geometry*. Birkhäuser.

### Conexão com o AXIOM
- `axiom tensor`: cálculo da métrica inversa, símbolos de Christoffel de segunda espécie $\Gamma^\mu_{\alpha\beta}$, tensor de curvatura de Riemann $R^\rho_{\sigma\mu\nu}$, tensor de Ricci $R_{\mu\nu}$, escalar de Ricci $R$ e tensor de Einstein $G_{\mu\nu}$.

---

## 9. Lógica Matemática, Teoria dos Conjuntos e Verificação Formal

### Ementa
Lógica proposicional e de primeira ordem (sintaxe, semântica, dedução natural, completude e compacidade), Teoria Axiomática dos Conjuntos (ZFC), ordinais e cardinais, Teoremas de Incompletude de Gödel, Teoria dos Tipos Dependentes (Cálculo de Construções Indutivas), correspondência de Curry-Howard, demonstração formal interativa de teoremas em Lean 4.

### Bibliografia Canônica
- **Mortari, C. A.** *Introdução à Lógica* (2ª edição). Editora Unesp.
- **Halmos, P. R.** *Naive Set Theory*. Springer.
- **Avigad, J., de Moura, L., Kong, S.** *Theorem Proving in Lean 4*. Lean Community.
- **Buzzard, K.** *Formalising Mathematics*. Imperial College London.

### Conexão com o AXIOM
- `axiom prove`: integração direta com o kernel do Lean 4 e Lake, rejeição de `sorry`/`admit`, auditoria de axiomas via `#print axioms` e detecção de tautologias reflexivas triviais (`rfl`).
- `axiom search-mathlib`: recuperação de declarações e lemas do Mathlib4 por assinatura de tipo.
