# Análise de Concorrência — MCPs de Matemática para Agentes (2026)

Mapeamento dos principais servidores MCP e frameworks de matemática para agentes de IA existentes no GitHub/PyPI em 2026 e o posicionamento diferencial do **AXIOM**.

---

## 1. Mapeamento dos Concorrentes Atuais

### A. Wrappers de Álgebra Simbólica e Cálculo (CAS)
* **[sdiehl/sympy-mcp](https://github.com/sdiehl/sympy-mcp)** *(Stephen Diehl)*
  * **Foco:** Conecta LLMs ao SymPy para álgebra, cálculo, EDOs e cálculo tensorial (relatividade geral).
  * **Limitação:** Retorna a saída bruta do SymPy sem verificador independente, sem hierarquia de garantias e sem integração com provadores formais.
* **[abhiphile/fermat-mcp](https://github.com/abhiphile/fermat-mcp)** *(Fermat MCP)*
  * **Foco:** Une SymPy (simbólico), NumPy (numérico/matrizes) e Matplotlib (gráficos) num único servidor MCP.
  * **Limitação:** Atua como calculadora multi-biblioteca; não audita se a resposta satisfaz a equação original, não diferencia aproximação numérica de identidade exata no protocolo e não possui suporte a Lean 4.
* **[codeprimate/math-mcp](https://github.com/codeprimate/math-mcp)** & **`math-mcp-learning-server`**
  * **Foco:** Servidores MCP utilitários com SymPy/SciPy para cálculos do dia a dia, estatística básica e matrizes no Claude Desktop/Cursor.
  * **Limitação:** Sem rastreabilidade de evidências (`Evidence`), sem detecção de contraexemplos e sem cadeia de pesquisa.

### B. Wrappers Proprietários (Wolfram)
* **[paraporoco/Wolfram-MCP](https://github.com/paraporoco/Wolfram-MCP)** & **[ricocf/mcp-wolframalpha](https://github.com/ricocf/mcp-wolframalpha)**
  * **Foco:** Ponte para o Wolfram Engine local ou API do WolframAlpha.
  * **Limitação:** Dependência de licença proprietária/API paga, caixa-preta (sem passos auditáveis abertos) e sem prova formal verificada por kernel independente.

### C. Servidores MCP Exclusivos de Prova Formal (Lean 4)
* **[project-numina/lean-lsp-mcp](https://github.com/project-numina/lean-lsp-mcp)** + **[cameronfreer/lean4-skills](https://github.com/cameronfreer/lean4-skills)**
  * **Foco:** Inspeção profunda do Lean 4 via LSP (`leanclient`), estado de metas (*goals*), diagnósticos e busca no Mathlib.
  * **Limitação:** Focado exclusivamente em escrita de provas Lean 4; não possui CAS (SymPy/Sage), cálculo numérico de precisão arbitrária, resolução direta de EDOs ou plotagem.
* **[KrystianYCSilva/lean-mcp](https://github.com/KrystianYCSilva/lean-mcp)**
  * **Foco:** Expõe uma única tool (`verify_lean_theorem`) para compilar teoremas Lean 4 via stdio.

---

## 2. Matriz Comparativa

| Capacidade / Diferencial | `sympy-mcp` | `fermat-mcp` | `Wolfram-MCP` | `lean-lsp-mcp` | **AXIOM** |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **100% Open Source (MIT)** | ✅ | ✅ | ❌ (Engine paga) | ✅ | ✅ |
| **Álgebra, Cálculo, EDOs, Matrizes, Otimização** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Prova Formal (Lean 4) + Bloqueio de `sorry`** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **Verificação Independente Obrigatória** | ❌ | ❌ | ❌ | Parcial (só Lean) | **✅ (Todos os domínios)** |
| **Hierarquia Explícita de Garantias (`Guarantee`)** | ❌ | ❌ | ❌ | ❌ | **✅ (6 níveis)** |
| **Proveniência & Comando Reprodutível (`Evidence`)** | ❌ | ❌ | ❌ | ❌ | **✅** |
| **Auditoria de Elo Mais Fraco (`chain_guarantee`)** | ❌ | ❌ | ❌ | ❌ | **✅ (`math_session`)** |
| **Auto-configuração de Agentes (`setup` / `doctor`)** | ❌ | ❌ | ❌ | ❌ | **✅ (Estilo REA)** |

---

## 3. Conclusão Estratégica (O "Oceano Azul" do AXIOM)

O mercado atual de MCPs matemáticos está dividido em **dois silos isolados**:
1. **Calculadoras CAS** (`sympy-mcp`, `fermat-mcp`, `math-mcp`) que apenas repassam comandos para o SymPy/NumPy sem verificar o resultado de forma independente.
2. **Provadores Formais Puros** (`lean-lsp-mcp`, `lean-mcp`) que exigem que o agente já saiba escrever Lean 4 diretamente, sem apoio de álgebra computacional ou análise numérica.

O **AXIOM** ocupa o espaço vazio entre esses dois mundos:
- **Não confia cegamente na engine**: toda integral é derivada de volta, toda raiz e EDO é substituída na equação original, toda decomposição matricial ($AA^{-1}=I$, $Av=\lambda v$, $PA=LU$) é conferida, e toda identidade passa por busca de contraexemplos em pontos transcendentais.
- **Une Computação + Verificação + Prova Formal sob o mesmo contrato**: o agente pode explorar uma conjectura numericamente (`math_explore`), simplificar simbolicamente (`math_simplify`), registrar na sessão com rastreamento de garantia (`math_session`) e auto-formalizar para o Lean 4 (`math_prove`).
