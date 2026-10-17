# Relatório de Validação e Integridade: Conjectura de Birch e Swinnerton-Dyer no AXIOM

Data de execução e consulta às fontes: 17 de outubro de 2026.  
Escopo: Validação analítica e numérica rigorosa de curvas elípticas sobre $\mathbb{Q}$ e corpos finitos $\mathbb{F}_p$, discriminantes de Weierstrass, pontos de torção de ordem 2, pontos racionais de ordem infinita em curvas de números congruentes ($E_5$), cotas de Hasse para o traço de Frobenius e controles negativos estritos sob o motor AXIOM v0.2.2.  
**Nenhuma demonstração da Conjectura de Birch e Swinnerton-Dyer geral foi fornecida ou produzida.** O Clay Mathematics Institute continua classificando o problema como aberto ([Página oficial do Clay](https://www.claymath.org/millennium/birch-and-swinnerton-dyer-conjecture/)).

---

## 1. Fundamentos e Resultados Obtidos

A Conjectura de Birch e Swinnerton-Dyer relaciona o posto algébrico do grupo abeliano de pontos racionais $E(\mathbb{Q}) \cong E(\mathbb{Q})_{\text{tors}} \oplus \mathbb{Z}^r$ à ordem do zero da função $L(E, s)$ em $s = 1$:

$$\text{ord}_{s=1} L(E, s) = r = \text{rank}(E(\mathbb{Q}))$$

### 1.1. Discriminante de Weierstrass e Suavidade
Para a equação reduzida de Weierstrass $y^2 = x^3 + ax + b$, a não-singularidade exige $\Delta = -16(4a^3 + 27b^2) \neq 0$:
- **Curva $E_1: y^2 = x^3 - x$ ($a=-1, b=0$)**: $\Delta = -16(4(-1)^3) = 64 \neq 0$. Comprovado como `exact-symbolic`.
- **Curva $E_5: y^2 = x^3 - 25x$ ($a=-25, b=0$)**: $\Delta = -16(4(-15625)) = 1.000.000$. Comprovado como `exact-symbolic`.
- **Curva Nodal Singular $y^2 = x^3 - 3x + 2$ ($a=-3, b=2$)**: $4(-3)^3 + 27(2)^2 = -108 + 108 = 0 \implies \Delta = 0$. O AXIOM comprovou a anulação do discriminante (`exact-symbolic`).
- **Controle negativo**: A afirmação de que a curva nodal possui discriminante liso $\Delta = 64$ foi refutada fail-closed (`unverified`, `passed = false`, resíduo 64).

### 1.2. Pontos de Ordem 2 (Subgrupo de Torção)
Os pontos de ordem 2 satisfazem $2P = \mathcal{O} \iff y = 0 \iff x^3 - x = 0$:
- O AXIOM resolveu algebricamente $x^3 - x = 0$, obtendo a tripla de raízes reais exatas $\{-1, 0, 1\}$ com garantia `exact-symbolic` e completude algébrica atestada pelo `solveset`.

### 1.3. Pontos Racionais de Ordem Infinita (Curva de Número Congruente $E_5$)
A curva $E_5: y^2 = x^3 - 25x$ tem posto algébrico $r = 1$, associada ao triângulo retângulo de lados $(9/2, 40/3, 41/6)$ e área 5:
- **Ponto Gerador $P = (-4, 6)$**: $(-4)^3 - 25(-4) = -64 + 100 = 36 = 6^2$. O AXIOM verificou a identidade analítica exata com garantia `exact-symbolic`.
- **Duplicação de Ponto $2P$ via Lei de Grupo**:
  $$2P = \left(\frac{1681}{144}, -\frac{62279}{1728}\right)$$
  O AXIOM comprovou a identidade $y^2 - (x^3 - 25x) \equiv 0$ com frações exatas e resíduo nulo (`exact-symbolic`).
- **Controle negativo de ponto espúrio**: Ponto incorreto $Q = (-4, 5)$ foi refutado com resíduo 11 (`status = disproven`, `unverified`, `passed = false`).

### 1.4. Cotas de Hasse para o Traço de Frobenius
Sobre o corpo finito $\mathbb{F}_p$, o número de pontos satisfaz o Teorema de Hasse:
$$|a_p| = |p + 1 - \#E(\mathbb{F}_p)| \le 2\sqrt{p}$$
- Para $E_1$ sobre $\mathbb{F}_3$: $\#E(\mathbb{F}_3) = 4 \implies a_3 = 3 + 1 - 4 = 0 \le 2\sqrt{3} \approx 3.464$. Validado simbolicamente.
- Para $E_1$ sobre $\mathbb{F}_5$: $\#E(\mathbb{F}_5) = 8 \implies a_5 = 5 + 1 - 8 = -2$. O AXIOM avaliou numericamente $2\sqrt{5} - 2 > 0$ comprovando a cota.
- **Controle negativo**: Violação fictícia da cota de Hasse ($a_5 = 10$) foi devidamente rejeitada.

### 1.5. Tratamento Fail-Closed da Conjectura Geral
Perante o comando `axiom solve "rank(E) - ord_s1(L(E, s)) = 0"`, o AXIOM recusou a resolução fechada de forma controlada (`unverified`, `ok: false`), reconhecendo o limite de decidabilidade de funções transcendentais não-avaliadas.

---

## 2. Resumo da Execução de Controle

Todos os 15 testes do script de validação foram aprovados com 100% de comportamento fail-closed:

| Verificação | Garantia AXIOM | `verification.passed` | Interpretação Científica |
|---|---|---|---|
| Autotestes do ambiente (`doctor`) | N/A | `true` | Ambiente íntegro e autotestes do núcleo aprovados |
| Discriminante $\Delta(E_1) = 64$ | `exact-symbolic` | `true` | Curva $E_1$ comprovada suave e não-singular |
| Discriminante $\Delta(E_5) = 1.000.000$ | `exact-symbolic` | `true` | Curva $E_5$ comprovada suave e não-singular |
| Discriminante $\Delta(\text{nodal}) = 0$ | `exact-symbolic` | `true` | Singularidade nodal detectada com precisão |
| Controle de suavidade falsa em curva nodal | `unverified` | `false` | Afirmação espúria refutada via contraexemplo |
| Raízes de torção de ordem 2 ($x \in \{-1, 0, 1\}$) | `exact-symbolic` | `true` | Solução algébrica completa e substituição verificada |
| Pertinência do ponto racional $P = (-4, 6)$ | `exact-symbolic` | `true` | Ponto racional em $E_5$ certificado independentemente |
| Pertinência do ponto duplicado $2P$ | `exact-symbolic` | `true` | Lei de adição de Weierstrass exata em $\mathbb{Q}$ |
| Controle negativo de ponto espúrio $Q = (-4, 5)$ | `unverified` | `false` | Ponto fora da curva refutado com resíduo 11 |
| Traço de Frobenius $a_3 = 0$ sobre $\mathbb{F}_3$ | `exact-symbolic` | `true` | Contagem exata de pontos sobre corpo finito |
| Verificação numérica da Cota de Hasse em $\mathbb{F}_5$ | `numerical-approximation` | `true` | $|a_5| = 2 \le 2\sqrt{5}$ confirmado |
| Controle de violação fictícia de Hasse | `unverified` | `false` | Afirmação impossível refutada fail-closed |
| Equação analítica geral do posto BSD | `unverified` | `false` / `None` | Recusa fail-closed perante problema aberto |
| MCP stdio: Verificação de ponto racional | `exact-symbolic` | `true` | Verificação via protocolo JSON-RPC 2.0 aprovada |
| MCP stdio: Refutação de ponto espúrio | `unverified` | `false` | Rejeição via protocolo JSON-RPC 2.0 confirmada |

---

## 3. Reprodutibilidade e Evidências

Para reproduzir integralmente os experimentos a partir da raiz do repositório:

```powershell
python reports/birch-and-swinnerton-dyer/validate.py
```

O script regera [`reports/birch-and-swinnerton-dyer/validation.json`](validation.json), contendo:
- Metadados de ambiente e hashes SHA-256 de todos os arquivos relevantes.
- Saídas JSON completas de todas as execuções CLI do AXIOM.
- Requisições e respostas JSON-RPC 2.0 completas do servidor MCP por stdio.
