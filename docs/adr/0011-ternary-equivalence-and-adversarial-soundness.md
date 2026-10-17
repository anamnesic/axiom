# ADR-0011: Semântica Ternária de Equivalência, Salvaguardas Adversariais e Restrições Relacionais

- **Status**: Aceito (Accepted)
- **Data**: 2026-10-17
- **Versão do AXIOM**: v0.2.2

## Contexto

A revisão da versão v0.2.1 identificou uma vulnerabilidade de solidez matemática (P0) e três melhorias arquiteturais essenciais (P1/P2):

1. **Falso Positivo por Amostragem Fixa em Identidades Universais**:
   No AXIOM v0.2.1, caso a redução simbólica da diferença entre duas expressões não reduzisse a zero, mas as primeiras 6 sondagens numéricas coincidissem com resíduo nulo, o verificador retornava `passed=True` com garantia `numerical-approximation`. O método `compare()` elevava esse resultado para `equivalent=True`.
   Isso permitia um contraexemplo adversarial de grau 6 construído sob medida para anular os pontos de teste fixos:
   $$P(x) = (x+1)(x-2)(x-i)(x+i)(x-1-i)(x+2)$$
   Onde $P(-1) = P(2) = P(i) = P(-i) = P(1+i) = P(-2) = 0$, porém $P(0) = 4 + 4i \neq 0$ e $P(3) = 400 - 200i \neq 0$. Amostras numéricas podem atestar concordância pontual (`consistent_with_samples`), mas **jamais** devem estabelecer equivalência universal sem demonstração formal ou algébrica.

2. **Gramática Relacional de Hipóteses**:
   Restrições relacionais comuns como `x!=1`, `x>0`, `x<=0` não eram interpretadas diretamente pelo parser de `assumptions`, forçando formatos redundantes de flags.

3. **Propagação de Hipóteses para Sistemas de Equações**:
   O resolvedor de sistemas (`solve_system`) não recebia o parâmetro `assumptions`, impedindo a filtragem de raízes espúrias fora do domínio pretendido em sistemas não-lineares.

4. **Qualificação Científica do Benchmark EXP-0001**:
   O caso TC-20 classificava a tautologia $2+2=2+2$ como matematicamente falsa por ser trivial em Lean (`by rfl`), misturando o critério de qualidade e profundidade da prova com o valor de verdade matemático.

## Decisões de Arquitetura

1. **Semântica Ternária de Equivalência (`proven`, `disproven`, `inconclusive`)**:
   - `proven`: A identidade é provada universalmente via redução simbólica canônica (`_is_symbolic_zero`) ou prova formal Lean 4 kernel-checked. Atribui `equivalent = True` e `guarantee = Guarantee.EXACT_SYMBOLIC`.
   - `disproven`: Um contraexemplo numérico/simbólico explícito foi descoberto ou a diferença polinomial foi demonstrada não-nula. Atribui `equivalent = False`, `guarantee = Guarantee.UNVERIFIED` e reporta `counterexample`.
   - `inconclusive`: Amostras numéricas coincidiram, mas a identidade universal não foi demonstrada algebricamente. Atribui `equivalent = False` (fail-closed), `consistent_with_samples = True`, `guarantee = Guarantee.UNVERIFIED` e `ver.passed = False`.

2. **Inspeção de Diferença Polinomial e Detecção de Contraexemplos**:
   - Para expressões com símbolos livres, `verify_equivalence` inspeciona a estrutura polinomial da diferença (`as_poly`).
   - Se o polinômio não for identicamente nulo, pelo Teorema Fundamental da Álgebra ele possui no máximo $d = \deg(P)$ raízes. O verificador expande ativamente as sondagens para além das primeiras 6 raízes até isolar um ponto de refutação inequívoco ($P(0) \neq 0, P(3) \neq 0$), rejeitando a afirmação de forma definitiva.

3. **Suporte a Restrições Relacionais no Parser**:
   - O `Parser` passa a reconhecer restrições relacionais no padrão `r"^([A-Za-z_]\w*)\s*(!=|<=|>=|<|>)\s*([+-]?\d+(?:\.\d+)?|[+-]?[A-Za-z_]\w*)$"`.
   - A sintaxe `x!=1` registra explicitamente o ponto excluído `1` e a restrição `x != 1`, permitindo certificar identidades com singularidades removíveis ($\frac{x-1}{x-1} = 1$) sob hipóteses explícitas sem erro de domínio.
   - Sintaxes como `x>0`, `x>=0`, `x<0`, `x<=0` e `x!=0` mapeiam automaticamente para as flags correspondentes (`positive`, `nonnegative`, `negative`, `nonpositive`, `nonzero`, `real`).

4. **Propagação de Hipóteses e Suporte Não-Linear em `solve_system`**:
   - `solve_system` recebe `assumptions`, repassa para o `Parser` e filtra tuplas de soluções que violem as propriedades dos símbolos (`_root_matches_symbol_assumptions`).
   - Adicionado fallback para `sp.nonlinsolve` em sistemas não-lineares, verificando cada solução remanescente por substituição exata.

5. **Revisão Metodológica do EXP-0001 e Registro Histórico**:
   - TC-20 redefinido para uma afirmação de fato matematicamente falsa admitida com `sorry` (`theorem fake_zero : 1 = 0 := by sorry`).
   - TC-21 introduzido com o polinômio adversarial de grau 6.
   - Relatórios anteriores (como P vs NP) devidamente anotados quanto ao contexto de versões anteriores e superação de limitações com `math.comb` e Pascal.

## Consequências

- **Soundness Absoluto**: Falsos positivos por colisão acidental de amostras numéricas em identidades universais são estruturalmente impossíveis.
- **Transparência**: Agentes recebem explicitamente o status (`proven`, `disproven` ou `inconclusive`) e o indicador `consistent_with_samples`.
- **Evolução do Benchmark EXP-0001**: 21 casos de teste, 0.0% FPR no AXIOM vs 46.2% no Naive CAS, mantendo 100% fail-closed e 45 testes automatizados aprovados no total.
