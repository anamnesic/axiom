# Tutorial Prático: Como Usar o Chronokairo AXIOM

> **One MCP for mathematical computation, exploration, and verification.**  
> *Research Math for All Time by [Chronokairo](https://chronokairo.com)*

Bem-vindo ao guia prático do **Chronokairo AXIOM**. Este tutorial ensina como instalar, configurar e utilizar o AXIOM tanto via **Linha de Comando (CLI)** quanto como **Servidor MCP (Model Context Protocol)** para agentes autônomos de Inteligência Artificial (Claude Desktop, Cursor, Antigravity, VS Code Copilot e Codex).

---

## 1. O que é o AXIOM?

O AXIOM não é apenas uma calculadora simbólica e nem apenas um assistente de prova. Ele é uma **infraestrutura de raciocínio matemático verificável**.

Quando um ser humano ou um modelo de IA resolve uma equação, simplifica uma expressão ou propõe um teorema, o AXIOM **nunca aceita a resposta sem uma auditoria independente**:
- **Soluções de equações** são substituídas de volta nas equações originais para comprovar resíduo simbólico estritamente nulo ($|f(r)| = 0$).
- **Integrais** são verificadas pelo Teorema Fundamental do Cálculo ($d/dx \int f = f$) ou quadratura numérica adaptativa de alta precisão.
- **Teoremas formais** são auditados diretamente no kernel do **Lean 4** via `#print axioms`, rejeitando furos (`sorry`), axiomas espúrios e tautologias superficiais.
- **Cadeias de raciocínio** em sessões de pesquisa são auditadas pelo princípio do elo mais fraco (*weakest-link principle*).

---

## 2. Instalação e Verificação do Ambiente

### Pré-requisitos
- **Python**: 3.10 ou superior (3.10, 3.11, 3.12).
- **Motores recomendados**: SymPy e mpmath (instalados automaticamente com o pacote).
- **Motores opcionais**: [Lean 4](https://lean-lang.org/) (via `elan`), SageMath, Julia.

### Instalação

Abra o terminal na pasta do projeto e instale em modo editável com as dependências de desenvolvimento:

```bash
git clone https://github.com/chronokairo/axiom.git
cd axiom
pip install -e ".[dev]"
```

### Auto-diagnóstico (`axiom doctor`)

Execute o diagnóstico automático para verificar a saúde dos motores e verificadores instalados:

```bash
axiom doctor
```

Você verá um resumo detalhado:
```text
┌─ AXIOM · doctor ─────────────────────────────────────────────────────────┐
│ Python          3.12.x                                                   │
│ Engine: sympy   AVAILABLE (sympy 1.14.0)                                 │
│ Engine: numeric AVAILABLE (mpmath 1.3.0)                                 │
│ Engine: lean    AVAILABLE / OPTIONAL                                     │
│ Verifiers       substitution, calculus, equivalence, sanity, tensor [OK] │
│ System Status   OPERATIONAL                                              │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Uso pela Linha de Comando (CLI)

O comando principal é `axiom`. Ele aceita várias sub-operações matemáticas.

### 3.1. Resolução Verificada de Equações (`axiom solve`)

Resolve a equação e **substitui cada raiz** para comprovar que $f(x) = 0$:

```bash
axiom solve "x^2 - 5*x + 6 = 0"
```
**Resultado esperado:**
- Raízes: `[2, 3]`
- Garantia: `[VERIFIED] VERIFIED-SUBSTITUTION` (resíduo 0.00e+00)

Para sistemas de equações com mais de uma variável:
```bash
axiom solve "x + y = 10; x - y = 2" --variable "x, y"
```

---

### 3.2. Simplificação e Identidades Simbólicas (`axiom simplify`)

Simplifica expressões com redução canônica:

```bash
axiom simplify "cos(x)^2 + sin(x)^2"
# Resultado: 1 (Garantia: EXACT-SYMBOLIC)

axiom simplify "(x^2 - 1)/(x - 1)"
# Resultado: x + 1 (com análise de domínio x != 1)
```

---

### 3.3. Cálculo: Derivadas e Integrais (`axiom diff`, `axiom integrate`)

**Derivada simbólica verificada:**
```bash
axiom diff "x^3 * sin(x)" --variable x
```

**Integral indefinida (verificada por derivação do resultado):**
```bash
axiom integrate "x * exp(-x)" --variable x
```

**Integral definida (com limites e verificação de quadratura):**
```bash
axiom integrate "sin(x)" --variable x --lower 0 --upper pi
# Resultado: 2 (Garantia: EXACT-SYMBOLIC)
```

---

### 3.4. Comparação e Detecção de Contraexemplos (`axiom compare`)

O comando `axiom compare` diferencia **igualdade formal exata** de **aproximação numérica**:

```bash
# Comparação simbólica exata
axiom compare "exp(i*pi)" "-1"
# Status: proven (Garantia: EXACT-SYMBOLIC)

# Comparação numérica com tolerância controlada
axiom compare "pi" "3.141592653589793" --tolerance 1e-12
# Status: approximately_equal (Garantia: NUMERICAL-APPROXIMATION)

# Refutação de falsa identidade com busca de contraexemplo
axiom compare "(x+1)*(x-2)*(x^2+1)" "0"
# Status: disproven (Garantia: UNVERIFIED, contraexemplo descoberto em x = 3)
```

---

### 3.5. Avaliação de Precisão Arbitrária (`axiom evaluate`)

Calcula constantes e expressões com até centenas de dígitos de precisão sem perda por ponto flutuante IEEE-754:

```bash
axiom evaluate "sqrt(2)" --precision 50
axiom evaluate "zeta(3)" --precision 80
```

---

### 3.6. Álgebra Linear e Geometria Diferencial (`axiom matrix`, `axiom tensor`)

**Determinante e autovalores:**
```bash
axiom matrix "[[1, 2], [3, 4]]" --operation det
axiom matrix "[[2, 0], [0, 5]]" --operation eigen
```

**Cálculo tensorial em variedade esférica $S^2$:**
```bash
axiom tensor "[[1, 0], [0, sin(theta)^2]]" --coordinates "theta, phi"
# Computa Christoffel, Riemann, Ricci e Escalar de Curvatura R = 2
```

---

### 3.7. Provas Formais com Lean 4 (`axiom prove`)

Valida declarações no assistente de prova interativo Lean 4:

```bash
axiom prove "theorem nat_add_comm (n m : Nat) : n + m = m + n := by omega" --engine lean
```
O AXIOM compila em um ambiente isolado, inspeciona o retorno de `#print axioms` e certifica que nenhum `sorry` foi introduzido.

---

### 3.8. Sessões de Pesquisa Encadeadas (`axiom session`)

Permite criar cadernos de pesquisa onde cada etapa depende das anteriores:

```bash
# 1. Iniciar nova sessão
axiom session new --title "Estudo de Raízes"

# 2. Registrar primeiro passo
axiom session record --step 1 --command "axiom solve 'x - 2 = 0'"

# 3. Registrar segundo passo dependente do passo 1
axiom session record --step 2 --command "axiom simplify '2^3'" --depends-on 1

# 4. Inspecionar integridade da cadeia (DAG)
axiom session status
```

Se o Passo 1 falhar, o Passo 2 é automaticamente marcado como não-confiável (`chain_valid = False`), protegendo conclusões subsequentes.

---

### 3.9. Visualização Gráfica (`axiom plot`)

Gera gráficos vetoriais autossuficientes em SVG (e exibe prévia em ASCII no terminal):

```bash
axiom plot "sin(x)/x" --range -10:10 --output sinc.svg
```

---

## 4. Usando o AXIOM como Servidor MCP em Agentes de IA

O AXIOM expõe **21 ferramentas matemáticas** via JSON-RPC 2.0 através do **Model Context Protocol (MCP)**.

### Configuração no Claude Desktop / Cursor / Antigravity

Adicione o AXIOM ao seu arquivo de configuração de MCP (por exemplo, `claude_desktop_config.json` ou as configurações de MCP do seu editor):

```json
{
  "mcpServers": {
    "axiom": {
      "command": "python",
      "args": ["-m", "axiom.mcp_server"],
      "env": {
        "AXIOM_ALLOWED_DIRS": "C:\\Users\\seu_usuario\\Desktop\\research"
      }
    }
  }
}
```

> **Dica de Segurança**: A variável `AXIOM_ALLOWED_DIRS` define quais diretórios o agente de IA tem permissão de acessar para leitura e gravação de arquivos de solução (`.json`, `.svg`, `.lean`). Tentativas de acessar arquivos fora dessas raízes serão bloqueadas fail-closed com `Permission denied`.

### As 21 Ferramentas MCP Disponíveis

| Ferramenta MCP | Descrição |
| :--- | :--- |
| `math_solve` | Resolve equações algébricas com verificação de substituição. |
| `math_solve_system` | Resolve sistemas lineares e não lineares com propagação de premissas. |
| `math_simplify` | Simplifica expressões simbólicas com análise de domínio. |
| `math_differentiate` | Derivação simbólica com verificação numérica de passo. |
| `math_integrate` | Integração definida e indefinida com verificação FTC e quadratura. |
| `math_limit` | Procura de limites bilaterais com detecção de descontinuidades. |
| `math_series` | Expansão em série de Taylor / Laurent com ordem especificada. |
| `math_compare` | Comparação de igualdade exata ou numérica com `--tolerance`. |
| `math_evaluate` | Avaliação com precisão arbitrária (`precision` dígitos). |
| `math_matrix` | Determinantes, inversas, autovalores e produto matricial. |
| `math_ode` | Resolução de EDOs com substituição da solução na equação. |
| `math_factorint` | Fatoração em números primos e teoria dos números. |
| `math_isprime` | Teste de primalidade rigoroso. |
| `math_optimize` | Otimização local e global com comprovação de derivadas nulas. |
| `math_tensor` | Geometria diferencial: Christoffel, Riemann, Ricci, curvatura escalar. |
| `math_prove` | Prova formal em Lean 4 auditada por kernel. |
| `math_verify` | Revalidação de arquivos JSON de resultados antigos. |
| `math_explain` | Explicação passo a passo da dedução matemática. |
| `math_explore` | Exploração de padrões e conjecturas em sequências numéricas. |
| `math_plot` | Renderização vetorial SVG de curvas matemáticas. |
| `math_search_mathlib`| Busca semântica local e online no acervo do Mathlib 4 via Loogle. |

---

## 5. Os 4 Estados Epistêmicos e Níveis de Garantia

Ao receber o retorno do AXIOM, inspecione sempre o campo `guarantee` do `MathResult`:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        QUATRO ESTADOS EPISTÊMICOS                      │
├─────────────────┬──────────────────────────────────────────────────────┤
│ 1. PROVA        │ formal-proof, exact-symbolic, verified-substitution │
│ 2. APROXIMAÇÃO  │ numerical-approximation                              │
│ 3. REFUTAÇÃO    │ unverified (status: disproven, com contraexemplo)   │
│ 4. INCONCLUSÃO  │ heuristic, sampled-visualization, catalog-lookup     │
└─────────────────┴──────────────────────────────────────────────────────┘
```

- **Nunca promova uma heurística ou aproximação a prova formal**.
- Se `verification.passed == False`, o resultado é categorizado como `unverified` e deve ser rejeitado para fins de demonstração rigorosa.

---

## 6. Exemplo de Sessão Prática para Agentes

Suponha que um agente queira verificar se o polinômio $P(x) = x^3 - 6x^2 + 11x - 6$ possui raiz em $x = 2$:

1. O agente invoca a ferramenta `math_solve`:
   ```json
   {
     "name": "math_solve",
     "arguments": {
       "expression": "x^3 - 6*x^2 + 11*x - 6 = 0",
       "variable": "x"
     }
   }
   ```
2. O AXIOM responde:
   ```json
   {
     "ok": true,
     "value": [1, 2, 3],
     "guarantee": "verified-substitution",
     "verification": {
       "passed": true,
       "method": "exact-substitution",
       "data": {
         "verified_solutions": ["1", "2", "3"],
         "max_residual": "0.00e+00"
       }
     }
   }
   ```
3. O agente tem a certeza matemática de que o conjunto $\{1, 2, 3\}$ é exato e validado por resíduo zero.

---

## 7. Como Contribuir e Testar

Para rodar todos os testes automatizados do projeto:

```bash
# Rodar todos os 63 testes unitários e adversariais
python -m pytest

# Rodar os testes adversariais específicos sem mocks
python -m pytest tests/test_adversarial.py -v

# Rodar a suíte dos Problemas do Milênio (105 critérios)
python benchmarks/millennium/run_millennium_bench.py

# Rodar a validação analítica de Navier-Stokes (19 critérios)
python reports/navier-stokes/validate.py
```

Para mais detalhes sobre arquitetura e decisões de projeto, consulte:
- [Documentação Geral (`README.md`)](file:///C:/Users/luann/Desktop/research/axiom/README.md)
- [Guia Detalhado de Casos de Uso (`docs/use-cases.md`)](file:///C:/Users/luann/Desktop/research/axiom/docs/use-cases.md)
- [Índice de Decisões de Arquitetura (`docs/adr/README.md`)](file:///C:/Users/luann/Desktop/research/axiom/docs/adr/README.md)
- [Auditoria de Gaps & Roadmap (`TODO.md`)](file:///C:/Users/luann/Desktop/research/axiom/TODO.md)
