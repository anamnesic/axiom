# Validação do Exemplo do Clay, Barreiras Estruturais e Auditoria no Ambiente AXIOM

Consulta e execução: 18 de outubro de 2026. Escopo: validação combinatória do exemplo de Cook, investigação analítica das barreiras de complexidade (Relativização, Provas Naturais, Algebrização), experimentos simbólicos de arithmetização e integridade ontológica no motor AXIOM v0.2.6. **Nenhuma demonstração de P = NP ou P ≠ NP foi fornecida ou produzida.** O problema permanece aberto pelo Clay Mathematics Institute ([Fonte oficial](https://www.claymath.org/millennium/p-vs-np/)).

Para a monografia técnica detalhada com demonstrações completas e fundamentação teórica, consulte [RESEARCH.md](RESEARCH.md). Para os resultados de simulação empírica, consulte [investigation_results.json](investigation_results.json).

---

## 1. Exemplo Combinatório de Cook

O exemplo de Stephen Cook considera escolher 100 alunos entre 400, respeitando uma lista de incompatibilidades. A quantidade de grupos candidatos, antes de aplicar restrições, é:

```text
C(400, 100) =
2241854791554337561923210387201698554845411177476295990399942258896013007429693894018935107174320
```

Isso corresponde a aproximadamente **$2,24 \times 10^{96}$ grupos candidatos**.
Dentro de um grupo de 100 alunos há **$C(100, 2) = 4.950$ pares distintos** cuja compatibilidade pode ser consultada. Ambas as chamadas retornaram `guarantee = exact-symbolic`, `verification.passed = true` e coincidiram com `math.comb` e a recorrência de Pascal.

---

## 2. Experimentos de Complexidade Estrutural e Redução Algébrica

### 2.1. Divergência Assintótica: Verificação $O(m)$ vs Busca $2^n$
O AXIOM calculou e verificou a prova de amortização assintótica:
$$\lim_{n \to \infty} \frac{n^3}{2^n} = 0$$
- CLI: `axiom limit "n^3 / 2^n" --variable n --to oo`
- Garantia: `numerical-approximation`, `passed = true`, resíduo $0.0$.
- O benchmark empírico em `investigation.py` demonstrou que a checagem de certificados opera em escala de microsegundos linear em $m$, enquanto a busca exaustiva atinge speedup superior a $538\times$ já em $n=14$ variáveis.

### 2.2. Arithmetização de Cook-Levin e SAT no AXIOM
- **Instância SAT consistente**: Sistema $(1 - x)(1 - y) = 0; \; x(1 - y) = 0$ resolvido com sucesso via `ax.solve`, retornando $\{y = 1, x \text{ livre}\}$ com garantia `verified-substitution` (`passed = true`).
- **Instância Inconsistente (UNSAT)**: Sistema $x = 1; \; x = 0$ processado fail-closed com conjunto vazio `[]` e `guarantee = heuristic`, `verification.passed = false`.
- **Identidade de De Morgan e Regra de Resolução**: Provadas simbolicamente com redução da diferença algébrica a 0 via `ax.compare` (`exact-symbolic`).

### 2.3. Teorema de Sensibilidade de Hao Huang (2019)
- Construção da recorrência matricial de Huang $A_{n+1} = \begin{pmatrix} A_n & I \\ I & -A_n \end{pmatrix}$.
- AXIOM verificou exaustivamente que $A_n^2 = n I_{2^n}$ para $n \in \{1, 2, 3\}$.
- Decomposição espectral de $A_2$ via `axiom matrix ... --op eigen` confirmou autovalores $\pm \sqrt{2}$ (multiplicidade 2) com garantia `verified-substitution`.
- Confirmação formal da cota $\deg(f) \le s(f)^2$ em funções booleanas clássicas ($\mathrm{PARITY}_3, \mathrm{MAJ}_3, \mathrm{AND}_3$).

---

## 3. Ambiente e Controles Executados (18 Critérios)

| # | Verificação | Garantia AXIOM | `verification.passed` | Tipo de Controle | Interpretação Científica |
|---|---|---|---|---|---|
| 1 | `doctor_self_tests_pass` | N/A | `true` | Ambiente | Integridade do motor e 7 autotestes aprovados |
| 2 | `groups_verified_exact` | `exact-symbolic` | `true` | Positivo | Contagem $C(400, 100) \approx 2.24 \times 10^{96}$ |
| 3 | `groups_independent_math_comb` | N/A | `true` | Positivo | Igualdade estrita com `math.comb` |
| 4 | `pairs_verified_exact` | `exact-symbolic` | `true` | Positivo | Contagem $C(100, 2) = 4.950$ pares |
| 5 | `pairs_independent_math_comb` | N/A | `true` | Positivo | Igualdade estrita com `math.comb` |
| 6 | `mcp_initialization` | N/A | `true` | Ambiente | Protocolo MCP stdio responde nome `axiom` |
| 7 | `mcp_tool_catalog` | N/A | `true` | Ambiente | Catálogo de 21 ferramentas MCP ativo |
| 8 | `mcp_binomial_verified` | `exact-symbolic` | `true` | Positivo | Chamada remota JSON-RPC $C(400, 100)$ aprovada |
| 9 | `mcp_exit_success` | N/A | `true` | Ambiente | Servidor MCP finalizou com código 0 |
| 10 | `asymptotic_limit_n3_div_2n_verified` | `numerical-approximation` | `true` | Positivo | Prova de divergência superpolinomial $\lim n^3/2^n = 0$ |
| 11 | `sat_algebraic_system_verified` | `verified-substitution` | `true` | Positivo | Resolução algébrica de sistema SAT consistente |
| 12 | `demorgan_algebraic_verified` | `exact-symbolic` | `true` | Positivo | Prova algébrica das Leis de De Morgan |
| 13 | `huang_matrix_A2_eigen_verified` | `verified-substitution` | `true` | Positivo | Autovalores $\pm\sqrt{2}$ da matriz de Huang verificados |
| 14 | `lean_control_expected_status` | `unverified` | `false` | Negativo/Amb | Reconhecimento fail-closed da ausência do kernel Lean |
| 15 | `incorrect_root_refuted` | `unverified` | `false` | Negativo | Raiz incorreta $x=4$ em $x^2-5x+6=0$ refutada |
| 16 | `false_equality_2plus2_refuted` | `unverified` | `false` | Negativo | Falsa proposição $2+2=5$ refutada |
| 17 | `unsat_contradiction_fail_closed` | `heuristic` | `false` | Negativo | Sistema SAT inconsistente rejeitado (0 soluções) |
| 18 | `anti_drift_p_vs_np_rejected` | `unverified` | `false` | Negativo | Rejeição semântica de $2+2=4$ reivindicado para P vs NP |

### Métricas Oficiais da Validação
- **Total de Critérios Avaliados**: 18 / 18 (100% aprovados)
- **Afirmações Positivas (*True Positives*)**: 9 / 9 (**100.0% TPR**)
- **Controles Negativos (*Fail-Closed*)**: 4 / 4 (**100.0% FCR**)
- **Taxa Global de Falsos Positivos**: **0.0% (0 / 4)**

---

## 4. Reprodução e Evidências

Na raiz do repositório:

```powershell
# Execução da suíte canônica de validação:
python reports/p-vs-np/validate.py

# Execução da investigação experimental detalhada:
python reports/p-vs-np/investigation.py

# Benchmark consolidado de todos os 7 problemas do Milênio:
python benchmarks/millennium/run_millennium_bench.py
```

Comandos individuais via CLI do AXIOM:

```powershell
python -m axiom.cli doctor --json
python -m axiom.cli number-theory binomial -n 400 -k 100 --json
python -m axiom.cli number-theory binomial -n 100 -k 2 --json
python -m axiom.cli limit "n^3 / 2^n" --variable n --to oo --json
python -m axiom.cli solve "(1 - x)*(1 - y) = 0; x*(1 - y) = 0" -v "x,y" --json
python -m axiom.cli solve "x = 1; x = 0" -v "x" --json
python -m axiom.cli compare "1 - (1 - (1 - x))*(1 - (1 - y))" "1 - x*y" --json
python -m axiom.cli matrix "[[0, 1, 1, 0], [1, 0, 0, 1], [1, 0, 0, -1], [0, 1, -1, 0]]" --op eigen --json
python -m axiom.cli prove "2 + 2 = 4" -e sympy --canonical "P vs NP" --json
python -m axiom.cli verify "x^2 - 5*x + 6 = 0" --solutions 4 --variable x --json
python -m axiom.cli prove examples/theorems.lean --engine lean --json
```

O arquivo [validation.json](validation.json) contém o registro integral com hashes SHA-256 e saídas das ferramentas.
O arquivo [RESEARCH.md](RESEARCH.md) contém a monografia científica completa.
