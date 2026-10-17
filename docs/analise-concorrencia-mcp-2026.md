# Panorama Competitivo e Ecossistema de Matemática para Agentes (2026)

Este documento mapeia de forma técnica e imparcial o ecossistema atual de matemática computacional e verificação formal para agentes de IA em 2026 — cobrindo tanto **servidores MCP** quanto **plataformas CAS e sistemas de prova formal fora do protocolo MCP** —, além de explicitar onde os concorrentes superam o **AXIOM (`v0.1.x`)** hoje.

---

## 1. Servidores MCP de Matemática (Ecossistema Direto)

### A. Sistemas de Álgebra Computacional (CAS) e Cálculo Numérico
* **[XBP-Europe/sagemath-mcp](https://github.com/XBP-Europe/sagemath-mcp)** *(SageMath MCP)*
  * **Pontos fortes:** Cerca de 40 ferramentas com sessão persistente sobre o **SageMath** (que integra GAP, PARI/GP, Singular e Maxima), oferecendo cobertura algébrica profunda (corpos de números, curvas elípticas, teoria de grupos, geometria algébrica) superior ao SymPy puro.
  * **Trade-offs:** Exige instalação local pesada do SageMath ou container Docker; retorna resultados da sessão Sage sem contrato de verificação cruzada independente nem auditoria de axiomas Lean 4.
* **[sdiehl/sympy-mcp](https://github.com/sdiehl/sympy-mcp)** *(Stephen Diehl)* & **[611711Dark/mcp_sympy_calculate_server](https://github.com/611711Dark/mcp_sympy_calculate_server)**
  * **Pontos fortes:** Projeto pioneiro e amplamente conhecido na comunidade; expõe diretamente álgebra simbólica, cálculo, EDOs e tensores (relatividade geral) do SymPy via FastMCP com estado de variáveis.
  * **Trade-offs:** Confia diretamente na saída do SymPy sem etapa de verificação independente (como derivar a primitiva ou substituir raízes) e sem distinção tipada entre aproximação numérica e identidade simbólica.
* **[abhiphile/fermat-mcp](https://github.com/abhiphile/fermat-mcp)** *(Fermat MCP)*
  * **Pontos fortes:** Combina SymPy (simbólico), NumPy (vetores/matrizes numéricas) e Matplotlib (visualização) em um único servidor FastMCP prático para uso geral.
  * **Trade-offs:** Atua como calculadora multi-biblioteca sem contrato de evidência ou verificação formal.
* **[codeprimate/math-mcp](https://github.com/codeprimate/math-mcp)** & **`math-mcp-learning-server`**
  * **Pontos fortes:** Leves e fáceis de instalar para aritmética, estatística básica e álgebra cotidiana no Claude Desktop e Cursor.
  * **Trade-offs:** Escopo utilitário; não voltados para pesquisa matemática verificável.

### B. Motores Proprietários (Wolfram)
* **[paraporoco/Wolfram-MCP](https://github.com/paraporoco/Wolfram-MCP)** & **[ricocf/mcp-wolframalpha](https://github.com/ricocf/mcp-wolframalpha)**
  * **Pontos fortes:** Conectam o agente ao **Wolfram Engine / Mathematica** ou à API do WolframAlpha, que possuem algoritmos simbólicos (integração de Risch completa, funções especiais hipergeométricas, bases de dados curadas) mais fortes que qualquer CAS puramente Python.
  * **Trade-offs:** Software proprietário/API paga, execução em caixa-preta (código-fonte dos algoritmos fechado) e ausência de verificação por kernel de prova formal (Lean 4).

### C. Servidores MCP de Prova Formal (Lean 4)
* **[project-numina/lean-lsp-mcp](https://github.com/project-numina/lean-lsp-mcp)** *(Project Numina)* + **[cameronfreer/lean4-skills](https://github.com/cameronfreer/lean4-skills)**
  * **Pontos fortes:** Referência madura para escrita interativa de provas em **Lean 4**. Conecta-se ao Language Server Protocol (`leanclient`) para inspecionar metas (*proof goals*) linha a linha, ler diagnósticos em tempo real, consultar documentação de *hover* e buscar teoremas via **Loogle**, **LeanSearch**, **LeanFinder** e *premise selection*.
  * **Onde supera o AXIOM hoje:** Possui inspeção interativa de estado de prova via LSP (tática por tática) e integração nativa com todo o fluxo de edição de projetos Mathlib4, enquanto o AXIOM `v0.1.x` executa verificação Lean 4 em lote (`lean` / `lake env lean` + `#print axioms`).
  * **Trade-offs:** É exclusivamente uma ferramenta de prova formal Lean 4 — não inclui CAS simbólico, avaliação numérica de precisão arbitrária, cálculo de tensores, EDOs ou geração de gráficos.
* **[KrystianYCSilva/lean-mcp](https://github.com/KrystianYCSilva/lean-mcp)**
  * **Pontos fortes:** Servidor mínimo focado em uma única ferramenta (`verify_lean_theorem`) para compilar blocos Lean 4.

---

## 2. Além do Protocolo MCP: Plataformas CAS e Sistemas de IA Formal

Comparar o AXIOM apenas com outros servidores MCP ignora as ferramentas que pesquisadores e agentes avançados já utilizam diretamente via terminal, Python sandbox ou integração de editor:

| Categoria | Principais Sistemas | O que fazem melhor que o AXIOM `v0.1.x` | Onde o AXIOM agrega valor complementar |
| :--- | :--- | :--- | :--- |
| **Plataformas CAS Completas** | **SageMath**, **Wolfram Mathematica**, **Maple**, **Julia (`Symbolics.jl`, `DifferentialEquations.jl`, `Oscar.jl`)** | Cobertura matemática muito mais ampla e madura (geometria algébrica, teoria de grupos finitos, cohomologia, EDOs/EDPs stiff em escala industrial). | Fornece um protocolo JSON-RPC padronizado com contrato `MathResult`, classificação explícita de garantia (`Guarantee`) e dupla checagem automática de cada resposta. |
| **Provers Formais com IA & RL** | **AlphaProof** (DeepMind), **DeepSeek-Prover-V2**, **Kimina-Prover** (Project Numina / Moonshot), **Lean Copilot / LeanDojo** | Geração autônoma de provas de nível olímpico (IMO / miniF2F / PutnamBench), busca em árvore (MCTS/RL) e sugestão interativa de táticas dentro do VS Code. | O AXIOM não é um modelo neural de busca de provas; é um *harness* determinístico que audita provas geradas pelo LLM (`#print axioms`) e combina CAS + numérico no mesmo fluxo. |
| **Sandboxes de Código para Agentes** | **OpenAI Code Interpreter**, **Claude Analysis Tool**, **[datalayer/jupyter-mcp-server](https://github.com/datalayer/jupyter-mcp-server)** | Liberdade total para o agente escrever scripts Python/SymPy/SciPy arbitrários em um kernel Jupyter persistente. | Sandboxes genéricos permitem que o LLM escreva código com bugs silenciosos (ex.: ignorar ramificações, aceitar `NaN` ou usar aproximações sem perceber); o AXIOM impõe parser AST seguro e verificadores independentes *fail-closed*. |

---

## 3. Matriz Comparativa Equilibrada (MCPs Matemáticos)

A tabela abaixo inclui tanto critérios de arquitetura de verificação quanto critérios de maturidade, profundidade algébrica e interatividade LSP onde os concorrentes levam vantagem:

| Critério Técnico | `sympy-mcp` | `sagemath-mcp` | `fermat-mcp` | `Wolfram-MCP` | `lean-lsp-mcp` | **AXIOM (`v0.1.x`)** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Licença Open Source** | ✅ (MIT) | ✅ | ✅ (MIT) | ❌ (Proprietário) | ✅ (MIT) | ✅ (MIT) |
| **Maturidade e Adoção da Comunidade** | Média-Alta | Média | Média | Alta (Engine) | **Alta (Padrão Lean)** | **Inicial (`v0.1.x`)** |
| **Profundidade em Álgebra Avançada / Teoria de Grupos** | Básica (SymPy) | **✅ Alta (Sage/GAP/PARI)** | Básica (SymPy) | **✅ Alta (Mathematica)** | ✅ (via Mathlib) | Básica-Média (SymPy) |
| **Inspeção Interativa de Metas Lean 4 via LSP (*Goal State*)** | ❌ | ❌ | ❌ | ❌ | **✅ Completa (LSP)** | ❌ (Verificação em lote) |
| **Busca de Teoremas Mathlib4 (Loogle / LeanSearch)** | ❌ | ❌ | ❌ | ❌ | **✅ Completa** | Parcial (Catálogo + Loogle) |
| **Cálculo Simbólico, EDOs, Matrizes, Tensores e Gráficos** | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Auditoria de Axiomas Lean 4 (`#print axioms` + cobertura)** | ❌ | ❌ | ❌ | ❌ | Manual pelo agente | **✅ Automática e obrigatória** |
| **Verificação Independente *Fail-Closed* no CAS** | ❌ | ❌ | ❌ | ❌ | N/A | **✅ (FTC, substituição, quadratura)** |
| **Separação Tipada: Simbólico Exato vs Evidência Numérica** | ❌ | ❌ | ❌ | ❌ | N/A | **✅ (`Guarantee` 6 níveis)** |
| **Sessões com Rastreamento do Elo Mais Fraco (`chain_guarantee`)** | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ (`math_session`)** |

---

## 4. Limitações Atuais do AXIOM (`v0.1.x`) e Quando Usar Outra Ferramenta

Para manter rigor científico e transparência com usuários e agentes:

1. **Estágio de maturidade (`v0.1.x`):** O AXIOM é um projeto recente focado na arquitetura de **contratos de verificação matemática**. Projetos como [`project-numina/lean-lsp-mcp`](https://github.com/project-numina/lean-lsp-mcp) e o próprio **SageMath** possuem anos de testes em produção e comunidades consolidadas.
2. **Construção interativa de provas longas em Lean 4:** Como o `LeanEngine` do AXIOM valida arquivos/trechos completos via `lake env lean` + `#print axioms` (sem manter um servidor LSP interativo aberto para inspecionar o *tactic state* linha a linha), **recomendamos usar o `lean-lsp-mcp` em conjunto com o AXIOM** quando o agente precisar construir provas longas passo a passo no Mathlib, usando o AXIOM para exploração simbólica/numérica prévia e auditoria final de axiomas.
3. **Domínios além do SymPy/mpmath:** Enquanto os adaptadores para SageMath e Julia no AXIOM operam como *bridges* opcionais, problemas pesados de geometria algébrica, teoria algébrica dos números ou elementos finitos são melhor atendidos diretamente pelo SageMath (`sagemath-mcp`) ou Julia (`SciML`).
4. **Proposta central do AXIOM:** O diferencial real do AXIOM não é substituir o SymPy, o SageMath ou o `lean-lsp-mcp`, mas fornecer uma **camada de integridade epistemológica** entre o agente e os motores matemáticos — garantindo que nenhuma aproximação numérica seja rotulada como identidade simbólica (`exact-symbolic`) e que nenhuma prova com `sorry`, axioma oculto ou arquivo sem teorema receba o selo `formal-proof`.
