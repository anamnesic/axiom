# 📐 Roteiro e Checklist de Verificação Matemática Formal
## Projeto de Prova Integral do Acervo `research/math` para Evolução do Chronokairo AXIOM

*Início:* Outubro de 2026 · *Meta:* Provar formalmente 1 Teorema/Seção por dia (120 Dias)  
*Filosofia:* **Paradigma REA (Investigate Mathematics)** — Não aceitar teoremas como premissas cegas; demonstrar todas as proposições no kernel formal do Lean 4 e nos motores computacionais (SymPy, Julia, mpmath).

---

## 🧭 Metodologia Diária de Investigação

Para cada dia do checklist:
1. **Escolha da Proposição:** Selecionar o teorema ou problema do livro correspondente.
2. **Isolamento e Versionamento:** Demonstrações preliminares e dados brutos de extração usam a pasta `build/` (ignorada no git). Provas formais aprovadas e reproduzíveis são versionadas em `research/arithmetic/` (rastreadas no Git) para que qualquer pesquisador e a suíte de CI possam recompilar e certificar independentemente cada teorema.
3. **Abertura de Sessão AXIOM:**
   ```bash
   axiom session new --name "dia-XX-nome" --title "Dia XX: Enunciado do Teorema"
   axiom session hypothesis --name "dia-XX-nome" "Enunciado matemático formal"
   ```
4. **Demonstração no Lean 4:** Codificar a prova sem buracos (`sorry`) em `research/arithmetic/dia_XX.lean` (ou `build/` durante a fase de rascunho).
5. **Auditoria e Certificação Kernel:**
   ```bash
   python -m axiom.cli prove research/arithmetic/dia_XX.lean
   ```
6. **Fechamento e Registro de Evidência:**
   ```bash
   axiom session complete --name "dia-XX-nome" --outcome "formal-proof"
   ```

---

## 📊 Progresso Geral

- **Total de Dias Planejados:** 120 dias
- **Teoremas Concluídos:** 12 / 120 (Livro 1 — Iniciação à Aritmética 100% concluído; Livro 3 — Passeio pelos Primos iniciado)
- **Status do Kernel:** Lean 4 v4.14.0 (CI) & v4.35.0 (local) (0 `sorry`, 0 axiomas não confiáveis)

---

## 📅 CHECKLIST DE EXECUÇÃO DIÁRIA

### Mês 1: Fundações, Aritmética e Teoria dos Números (Dias 01 a 30)
*Obras de Referência:*
- *Iniciação à Aritmética* — Abramo Hefez (SBM / OBMEP)
- *Fundamentos de Aritmética* — Hygino H. Domingues
- *Teoria dos Números: Um Passeio pelos Primos* — Brochero et al.
- *A Construção dos Números Reais* — Aguilar & Dias
- *Fundamentos da Matemática Elementar (FME)* — Gelson Iezzi et al.

- [x] **Dia 01:** Linearidade e Transitividade da Divisibilidade em $\mathbb{Z}$ (*Hefez, Cap. 3.3*)
  - *Teoremas:* `hefez_dvd_linear_comb`, `hefez_dvd_trans`.
  - *Garantia:* `formal-proof` (Lean 4) + SymPy.
- [x] **Dia 02:** Algoritmo da Divisão Euclidiana (*Hefez, Cap. 3.4*)
  - *Teorema:* $\forall a, b \in \mathbb{N}, b > 0 \implies a = bq + r \land r < b$ (`hefez_euclidean_division`).
  - *Garantia:* `formal-proof` (Lean 4) + 1.000 amostras SymPy.
- [x] **Dia 03:** MDC de Números Consecutivos e Coprimaridade de $n$ e $2n+1$ (*Hefez, Cap. 3.3*)
  - *Teoremas:* `hefez_gcd_succ`, `hefez_gcd_two_n_plus_one`, `hefez_common_divisor_sub`.
  - *Garantia:* `formal-proof` (Lean 4).
- [x] **Dia 04:** Identidade de Bézout e Algoritmo Estendido de Euclides (*Hefez, Cap. 3.8 & 3.9 / Hygino, Cap. 3*)
  - *Teoremas:* `Dia04Bezout.hefez_bezout_identity`, `Dia04Bezout.hefez_common_divisor_divides_gcd`, `Dia04Bezout.xgcd`.
  - *Garantia:* `formal-proof` (Lean 4 kernel, 0 sorry) + retrosubstituição construtiva de Euclides.
- [x] **Dia 05:** Lema de Euclides para Números Primos (*Hefez, Cap. 2.6 / 3.9*)
  - *Teoremas:* `Dia05EuclidLemma.hefez_coprime_dvd_mul`, `Dia05EuclidLemma.hefez_prime_gcd_cases`, `Dia05EuclidLemma.hefez_euclid_lemma`.
  - *Garantia:* `formal-proof` (Lean 4 kernel, 0 sorry, axiomas padrão `propext`, `Quot.sound`).
- [x] **Dia 06:** Teorema Fundamental da Aritmética — Existência da Decomposição em Primos (*Hefez, Cap. 2.1–2.3*)
  - *Teoremas:* `Dia06TFAExistence.hefez_fundamental_theorem_existence`, `Dia06TFAExistence.primeFactors`, `Dia06TFAExistence.minFac`.
  - *Garantia:* `formal-proof` (Lean 4 kernel, 0 sorry, indução forte `Nat.strongRecOn`) + decomposição construtiva (`primeFactors 360 = [2, 2, 2, 3, 3, 5]`) e revalidação de sessão (`dia-06-tfa-existence`).
- [x] **Dia 07:** Teorema Fundamental da Aritmética — Unicidade da Decomposição (*Hefez, Cap. 2.1–2.3*)
  - *Teoremas:* `Dia07TFAUniqueness.hefez_fundamental_theorem_uniqueness`, `Dia07TFAUniqueness.prime_mem_of_dvd_prod`, `Dia07TFAUniqueness.prod_split`.
  - *Garantia:* `formal-proof` (Lean 4 kernel, 0 sorry, 14 teoremas auditados, `List.Perm`) + verificação de invariância de permutação e revalidação de sessão (`dia-07-tfa-uniqueness`).
- [x] **Dia 08:** Teorema de Euclides: Infinitude dos Números Primos (*Hefez, Cap. 2.4*)
  - *Teoremas:* `Dia08EuclidInfinitude.hefez_euclid_infinitude_primes`, `Dia08EuclidInfinitude.hefez_primes_unbounded`, `Dia08EuclidInfinitude.minFac_prime`, `Dia08EuclidInfinitude.exists_prime_dvd`, `Dia08EuclidInfinitude.dvd_fact`, `Dia08EuclidInfinitude.prime_dvd_consecutive`.
  - *Garantia:* `formal-proof` (Lean 4 kernel, 0 sorry, 17 lemas/exemplos auditados) + expansão de primitiva computacional `nextprime` no AXIOM e revalidação de sessão (`dia-08-euclid-infinitude`).
- [x] **Dia 09:** Equações Diofantinas Lineares em Duas Variáveis (*Hefez, Cap. 3.10*)
  - *Teoremas:* `Dia09Diophantine.diophantine_dvd_c`, `Dia09Diophantine.diophantine_particular_solution`, `Dia09Diophantine.coprime_dvd_mul_int`, `Dia09Diophantine.diophantine_general_valid`, `Dia09Diophantine.hefez_diophantine_complete`, `Dia09Diophantine.diophantine_general_iff`, `Dia09Diophantine.hefez_selos_valid`.
  - *Garantia:* `formal-proof` (Lean 4 kernel, 0 sorry, Teorema 3.5 de Hefez com 10 teoremas/exemplos auditados) + verificação de XGCD(3, 5) e retrovalidação de sessão (`dia-09-diophantine`).
- [x] **Dia 10:** Relações de Congruência e Aritmética Modular $\mathbb{Z}/m\mathbb{Z}$ (*Hefez, Cap. 4*)
  - *Teoremas:* `Dia10Congruences.cong_refl`, `Dia10Congruences.cong_symm`, `Dia10Congruences.cong_trans`, `Dia10Congruences.cong_add`, `Dia10Congruences.cong_sub`, `Dia10Congruences.cong_mul`, `Dia10Congruences.cong_pow`, `Dia10Congruences.invertible_of_bezout`, `Dia10Congruences.bezout_of_invertible`, `Dia10Congruences.common_divisor_dvd_one_of_invertible`.
  - *Garantia:* `formal-proof` (Lean 4 kernel, 0 sorry, relação de equivalência, compatibilidade algébrica aditiva/multiplicativa/potências e inversos modulares via Bézout com 12 teoremas/exemplos auditados) + Teorema Chinês dos Restos e retrovalidação de sessão (`dia-10-congruences`).
  - 🎉 **Marco Concluído:** **100% dos tópicos e teoremas fundamentais selecionados do Livro 1 (*Iniciação à Aritmética*, Abramo Hefez) formalizados e verificados.**
- [x] **Dia 11:** Pequeno Teorema de Fermat (*Brochero et al., Cap. 3 / Hefez, Cap. 4*)
  - *Teoremas:* `Dia11Fermat.succ_mul_binom_succ`, `Dia11Fermat.prime_dvd_binom`, `Dia11Fermat.bsum_mul_add`, `Dia11Fermat.bsum_eq_pow`, `Dia11Fermat.dvd_bsum_sub_one`, `Dia11Fermat.cong_succ_pow`, `Dia11Fermat.fermat_little_congruence` ($a^p \equiv a \pmod p$), `Dia11Fermat.fermat_little_coprime` ($a^{p-1} \equiv 1 \pmod p$).
  - *Garantia:* `formal-proof` (Lean 4 kernel v4.14.0 CI / v4.35.0 local, 0 sorry, 0 axiomas ad-hoc, 34 teoremas/exemplos auditados) + expansão binomial de Newton construtiva e retrovalidação de sessão (`dia-11-fermat`).
- [x] **Dia 12:** Teorema de Wilson (*Brochero et al., §1.6, Lema 1.33 e Teorema 1.34, pp. 43–44*)
  - *Teoremas:* `Dia12Wilson.inverse_exists`, `Dia12Wilson.inverse_unique`, `Dia12Wilson.self_inverse`, `Dia12Wilson.paired_product`, `Dia12Wilson.wilson_forward`, `Dia12Wilson.wilson_converse`, `Dia12Wilson.wilson_iff`, `Dia12Wilson.wilson_congruence`: para $p \ge 2$, $p$ é primo se e somente se $(p-1)! \equiv -1 \pmod p$.
  - *Garantia da proposição Lean:* `formal-proof` (Lean 4 v4.14.0 / v4.35.0; 31 teoremas auditados; 0 sorry; apenas `propext`, `Classical.choice`, `Quot.sound`). Pareamento de inversos via Bézout, sem Mathlib nem `Int.emod`; caso $p=1$ excluído explicitamente.
  - *Evidências:* [`reports/dia-12-wilson/REPORT.md`](../reports/dia-12-wilson/REPORT.md), manifesto SHA-256 e sessão local `dia-12-wilson`. Alinhamento automático com a descrição em prosa permanece `candidate`/`unverified`, separado do certificado de kernel.
- [ ] **Dia 13:** Teorema Chinês dos Restos
  - *Meta:* Solução simultânea de congruências com módulos coprimos dois a dois.
- [ ] **Dia 14:** Função Totiente de Euler $\phi(n)$ e Multiplicatividade (*Brochero, Cap. 4*)
  - *Meta:* $\gcd(m, n) = 1 \implies \phi(mn) = \phi(m)\phi(n)$.
- [ ] **Dia 15:** Teorema de Euler: Generalização de Fermat
  - *Meta:* $\gcd(a, m) = 1 \implies a^{\phi(m)} \equiv 1 \pmod m$.
- [ ] **Dia 16:** Princípio de Indução Matemática Fraca e Forte (*Hygino Domingues, Cap. 1*)
  - *Meta:* Provar a equivalência lógica entre indução matemática e boa ordem.
- [ ] **Dia 17:** Princípio da Boa Ordem dos Naturais
  - *Meta:* Todo subconjunto não vazio de $\mathbb{N}$ possui um menor elemento.
- [ ] **Dia 18:** Fórmulas Fechadas para Somas de Potências
  - *Meta:* $\sum_{i=1}^n i = \frac{n(n+1)}{2}$ e $\sum_{i=1}^n i^2 = \frac{n(n+1)(2n+1)}{6}$.
- [ ] **Dia 19:** Binômio de Newton e Relação Fundamental de Stifel (*FME Vol 4*)
  - *Meta:* $\binom{n+1}{k} = \binom{n}{k-1} + \binom{n}{k}$ e expansão de $(a+b)^n$.
- [ ] **Dia 20:** Desigualdade de Bernoulli
  - *Meta:* $\forall x > -1, (1 + x)^n \ge 1 + nx$ para todo $n \in \mathbb{N}$.
- [ ] **Dia 21:** Construção dos Inteiros $\mathbb{Z}$ via Pares Ordenados (*Aguilar & Dias, Cap. 1*)
  - *Meta:* Provar que $\mathbb{N} \times \mathbb{N} / \sim$ satisfaz os axiomas de anel comutativo ordenado.
- [ ] **Dia 22:** Construção dos Racionais $\mathbb{Q}$ como Corpo de Frações
  - *Meta:* Existência de inversos multiplicativos para elementos não nulos.
- [ ] **Dia 23:** Irracionalidade de $\sqrt{2}$ e Incompletude de $\mathbb{Q}$
  - *Meta:* Não existe $q \in \mathbb{Q}$ tal que $q^2 = 2$.
- [ ] **Dia 24:** Cortes de Dedekind e Propriedade do Supremo em $\mathbb{R}$ (*Aguilar & Dias, Cap. 3*)
  - *Meta:* Todo conjunto não vazio e limitado superiormente em $\mathbb{R}$ possui supremo.
- [ ] **Dia 25:** Propriedade Arquimediana dos Números Reais
  - *Meta:* $\forall x \in \mathbb{R}, \exists n \in \mathbb{N}: n > x$.
- [ ] **Dia 26:** Densidade de $\mathbb{Q}$ e dos Irracionais em $\mathbb{R}$
  - *Meta:* Entre quaisquer dois reais distintos existe um racional e um irracional.
- [ ] **Dia 27:** Módulo e Desigualdade Triangular em $\mathbb{C}$ (*Molter & Zahn*)
  - *Meta:* $|z_1 + z_2| \le |z_1| + |z_2|$ e $|z_1 z_2| = |z_1| |z_2|$.
- [ ] **Dia 28:** Fórmula de De Moivre e Raízes da Unidade
  - *Meta:* $(\cos \theta + i \sin \theta)^n = \cos(n\theta) + i \sin(n\theta)$.
- [ ] **Dia 29:** Teorema das Raízes Racionais de Polinômios Inteiros (*FME Vol 6*)
  - *Meta:* Se $p/q$ é raiz de $\sum a_k x^k$, então $p \mid a_0$ e $q \mid a_n$.
- [ ] **Dia 30:** Relações de Girard entre Raízes e Coeficientes
  - *Meta:* Fórmulas simétricas elementares para polinômios de grau $n$.

---

### Mês 2: Lógica, Conjuntos e Álgebra Abstrata (Dias 31 a 60)
*Obras de Referência:*
- *Introdução à Lógica* — Cezar A. Mortari
- *Introdução aos Fundamentos da Matemática* — Newton da Costa
- *Teoria Ingênua dos Conjuntos* — Paul Halmos
- *Álgebra: Um Curso de Introdução* — Arnaldo Garcia & Yves Lequain
- *Álgebra Linear* — Elon Lages Lima (IMPA)

- [ ] **Dia 31:** Leis de De Morgan Generalizadas para Famílias de Conjuntos
- [ ] **Dia 32:** Relações de Equivalência, Classes e Partições (*Halmos, Seção 7*)
- [ ] **Dia 33:** Teorema da Injetividade, Sobrejetividade e Existência de Inversa
- [ ] **Dia 34:** Teorema de Cantor: $|A| < |\mathcal{P}(A)|$ (Cardinalidade dos Subconjuntos)
- [ ] **Dia 35:** Enumerabilidade de $\mathbb{Q}$ e Não Enumerabilidade de $\mathbb{R}$
- [ ] **Dia 36:** Lema de Zorn e Teorema de Zermelo (Axioma da Escolha)
- [ ] **Dia 37:** Definição de Grupo: Unicidade da Identidade e dos Inversos (*Garcia & Lequain*)
- [ ] **Dia 38:** Critério de Subgrupo e Interseção de Subgrupos
- [ ] **Dia 39:** Classes Laterais e Teorema de Lagrange: $|G| = [G:H] \cdot |H|$
- [ ] **Dia 40:** Grupos Cíclicos: Todo subgrupo de um grupo cíclico é cíclico
- [ ] **Dia 41:** Subgrupos Normais e Boa Definição do Grupo Quociente $G/N$
- [ ] **Dia 42:** Primeiro Teorema dos Isomorfismos de Grupos ($G/\ker \phi \cong \operatorname{Im} \phi$)
- [ ] **Dia 43:** Grupos Simétricos $S_n$: Decomposição em Transposições e Sinal de Permutação
- [ ] **Dia 44:** Anéis: Leis Distributivas e Elemento Nulo Anulador ($0 \cdot a = 0$)
- [ ] **Dia 45:** Domínios de Integridade e Lei do Cancelamento do Produto
- [ ] **Dia 46:** Ideais e Construção de Anéis Quocientes $R/I$
- [ ] **Dia 47:** Ideais Primos vs. Ideais Maximais em Anéis Comutativos
- [ ] **Dia 48:** Domínios de Ideais Principais (DIP) e Propriedade de Fatoração Única
- [ ] **Dia 49:** Corpos e Extensões Simples $F(\alpha)$
- [ ] **Dia 50:** Teorema da Torre de Corpos: $[K:F] = [K:E][E:F]$
- [ ] **Dia 51:** Espaços Vetoriais: Independência Linear e Teorema do Span (*Elon Lages Lima*)
- [ ] **Dia 52:** Teorema da Base e Invariância da Dimensão em Espaços Finitamente Gerados
- [ ] **Dia 53:** Teorema do Núcleo e da Imagem: $\dim V = \dim \ker T + \dim \operatorname{Im} T$
- [ ] **Dia 54:** Matriz de uma Transformação Linear e Isomorfismo $\mathcal{L}(V, W) \cong M_{m \times n}$
- [ ] **Dia 55:** Determinantes: Caracterização Multilinear Alternada e Unicidade
- [ ] **Dia 56:** Invertibilidade: Matriz $A$ é inversível se e somente se $\det(A) \ne 0$
- [ ] **Dia 57:** Autovalores, Autovetores e Polinômio Característico
- [ ] **Dia 58:** Teorema de Cayley-Hamilton ($P_A(A) = 0$)
- [ ] **Dia 59:** Espaços com Produto Interno e Desigualdade de Cauchy-Schwarz
- [ ] **Dia 60:** Algoritmo de Ortogonalização de Gram-Schmidt

---

### Mês 3: Análise Real e Cálculo Diferencial/Integral (Dias 61 a 90)
*Obras de Referência:*
- *Curso de Análise Vol. 1* — Elon Lages Lima (IMPA / Projeto Euclides)
- *Introdução à Análise Matemática* — Geraldo Ávila
- *Curso de Análise Real* — Cassio Neri & Marco Cabral (UFRJ)

- [ ] **Dia 61:** Limite de Sequências: Definição $\varepsilon$-$N$ e Unicidade do Limite
- [ ] **Dia 62:** Toda Sequência Monótona e Limitada Converge em $\mathbb{R}$
- [ ] **Dia 63:** Teorema de Bolzano-Weierstrass para Sequências Reais
- [ ] **Dia 64:** Critério de Cauchy e Completude dos Números Reais
- [ ] **Dia 65:** Testes de Convergência de Séries: Teste da Comparação e Razão de d'Alembert
- [ ] **Dia 66:** Limites de Funções: Critério $\varepsilon$-$\delta$ e Caracterização por Sequências
- [ ] **Dia 67:** Teorema da Conservação do Sinal para Funções Contínuas
- [ ] **Dia 68:** Teorema do Valor Intermediário (Bolzano) para Intervalos Conexos
- [ ] **Dia 69:** Teorema de Weierstrass: Máximos e Mínimos Globais em Compactos
- [ ] **Dia 70:** Teorema de Heine-Borel: Continuidade Uniforme em Conjuntos Compactos
- [ ] **Dia 71:** Definição Rigorosa de Derivada e Regra da Cadeia
- [ ] **Dia 72:** Teorema de Fermat sobre Pontos Críticos ($f'(x_0) = 0$)
- [ ] **Dia 73:** Teorema de Rolle
- [ ] **Dia 74:** Teorema do Valor Médio de Lagrange
- [ ] **Dia 75:** Teorema do Valor Médio de Cauchy e Regra de L'Hôpital
- [ ] **Dia 76:** Fórmula de Taylor com Resto de Lagrange
- [ ] **Dia 77:** Convexidade e Teste da Segunda Derivada ($f''(x) \ge 0$)
- [ ] **Dia 78:** Integral de Darboux: Somas Superiores e Inferiores
- [ ] **Dia 79:** Critério de Integrabilidade de Riemann
- [ ] **Dia 80:** Teorema Fundamental do Cálculo (Partes 1 e 2)
- [ ] **Dia 81:** Fórmula de Integração por Partes e Mudança de Variável
- [ ] **Dia 82:** Convergência Pontual vs. Convergência Uniforme de Funções
- [ ] **Dia 83:** Teorema da Continuidade do Limite Uniforme
- [ ] **Dia 84:** Teorema da Integração do Limite Uniforme: $\lim \int f_n = \int \lim f_n$
- [ ] **Dia 85:** Teste $M$ de Weierstrass para Convergência Uniforme de Séries
- [ ] **Dia 86:** Séries de Potências e Fórmula de Cauchy-Hadamard para o Raio
- [ ] **Dia 87:** Derivação Termo a Termo de Séries de Potências no Interior do Disco
- [ ] **Dia 88:** Topologia do $\mathbb{R}^n$: Abertos, Fechados e Compacidade por Heine-Borel
- [ ] **Dia 89:** Diferenciabilidade no $\mathbb{R}^n$ e Matriz Jacobiana
- [ ] **Dia 90:** Teorema de Schwarz: Simetria das Derivadas Mistas $\frac{\partial^2 f}{\partial x \partial y} = \frac{\partial^2 f}{\partial y \partial x}$

---

### Mês 4: Análise no $\mathbb{R}^n$, EDOs, Análise Complexa e Geometria (Dias 91 a 120)
*Obras de Referência:*
- *Análise no Espaço $\mathbb{R}^n$* e *Curso de Análise Vol. 2* — Elon Lages Lima
- *Equações Diferenciais Elementares* — Boyce & DiPrima / Djairo de Figueiredo
- *Cálculo em uma Variável Complexa* — Marcio G. Soares (IMPA)
- *Geometria Diferencial de Curvas e Superfícies* — Manfredo P. do Carmo
- *Medida e Integração* — Pedro J. Fernandez (IMPA)

- [ ] **Dia 91:** Teorema do Ponto Fixo de Banach para Espaços Métricos Completos
- [ ] **Dia 92:** Teorema da Função Inversa no $\mathbb{R}^n$
- [ ] **Dia 93:** Teorema da Função Implícita no $\mathbb{R}^n$
- [ ] **Dia 94:** Método dos Multiplicadores de Lagrange para Extremos Vinculados
- [ ] **Dia 95:** Integrais Múltiplas e Teorema de Fubini para Funções Contínuas
- [ ] **Dia 96:** Mudança de Variáveis em Integrais Múltiplas com Fator Jacobiano
- [ ] **Dia 97:** Teorema de Green no Plano
- [ ] **Dia 98:** Teorema da Divergência de Gauss no $\mathbb{R}^3$
- [ ] **Dia 99:** Teorema Clássico de Stokes no Espaço
- [ ] **Dia 100:** Teorema de Existência e Unicidade de Picard-Lindelöf para EDOs
- [ ] **Dia 101:** EDOs Lineares de 1ª Ordem via Fator Integrante
- [ ] **Dia 102:** EDOs Lineares Homogêneas de 2ª Ordem e Não Anulamento do Wronskiano
- [ ] **Dia 103:** Método da Variação de Parâmetros para Soluções Particulares
- [ ] **Dia 104:** Equações Diferenciais Exatas e Existência de Potenciais
- [ ] **Dia 105:** Transformada de Laplace: Propriedades de Linearidade e Deslocamento
- [ ] **Dia 106:** Condições de Cauchy-Riemann para Funções Complexas Diferenciáveis
- [ ] **Dia 107:** Holomorfia Implica Analiticidade Local
- [ ] **Dia 108:** Teorema Integral de Cauchy para Caminhos Fechados
- [ ] **Dia 109:** Fórmula Integral de Cauchy e Derivadas Complexas de Ordem Superior
- [ ] **Dia 110:** Teorema de Liouville e Demonstração do Teorema Fundamental da Álgebra
- [ ] **Dia 111:** Teorema dos Resíduos de Cauchy e Cálculo de Integrais Reais
- [ ] **Dia 112:** Princípio do Módulo Máximo para Funções Holomorfas
- [ ] **Dia 113:** Triedro de Frenet-Serret para Curvas Parametrizadas por Comprimento de Arco
- [ ] **Dia 114:** Teorema Fundamental da Teoria Local de Curvas (Curvatura e Torção)
- [ ] **Dia 115:** Primeira e Segunda Formas Fundamentais de uma Superfície Regular
- [ ] **Dia 116:** Curvatura Gaussiana $K$ e Curvatura Média $H$
- [ ] **Dia 117:** *Theorema Egregium* de Gauss: A Curvatura Gaussiana é Invariante Isométrico
- [ ] **Dia 118:** Equações Diferenciais das Geodésicas sobre Superfícies
- [ ] **Dia 119:** Teorema de Gauss-Bonnet Local para Triângulos Geodésicos
- [ ] **Dia 120:** Teorema de Gauss-Bonnet Global: $\iint_S K \, dA = 2\pi \chi(S)$

---

## 🛠️ Contribuição Direta para a Arquitetura do AXIOM

A cada bloco de 10 dias concluído:
1. Novos padrões e táticas Lean 4 são catalogados na skill [`skills/formal/writing-lean-proofs`](../axiom/skills/formal/writing-lean-proofs/SKILL.md).
2. Casos de teste de regressão e invariantes são incorporados em [`tests/`](../axiom/tests/).
3. O AXIOM ganha capacidade comprovada de assistir pesquisadores e matemáticos em ambientes de ensino e pesquisa de ponta.
