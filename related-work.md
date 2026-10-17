# Trabalhos Relacionados e Comparação Científica — AXIOM

Este documento situa o **Chronokairo AXIOM** no panorama da literatura científica e do ecossistema tecnológico contemporâneo (2024–2026), comparando sua arquitetura neuro-simbólica com sistemas de álgebra computacional (CAS), assistentes de prova formal (ITPs) e ferramentas para agentes autônomos baseados em LLMs.

---

## 1. Panorama da Literatura Científica

### 1.1. Modelos de Linguagem para Raciocínio Matemático
O avanço do raciocínio matemático em inteligência artificial tem sido impulsionado por modelos especializados:
- **Minerva (Lewkowycz et al., NeurIPS 2022)**: Treinado sobre artigos do arXiv e páginas web com MathJax, demonstrando que o pré-treinamento técnico e o uso de amostragem majoritária (*majority voting / self-consistency*) aumentam o desempenho em álgebra e cálculo elementar. Limitação: Ausência de verificação simbólica determinística; susceptível a alucinações aritméticas e falsas passagens lógicas.
- **Llemma (Azerbayev et al., ICLR 2024)**: Modelo de base aberto de 7B e 34B parâmetros adaptado para matemática e formalização em Lean, Isabelle e Python. Embora eficaz na geração de código formal, não inclui um motor de execução e auditoria em tempo de inferência.
- **DeepSeek-Math / InternLM-Math (Shao et al., 2024)**: Aperfeiçoamento de Chain-of-Thought e fine-tuning com feedback de código (GRPO/PPO), atingindo alta acurácia em benchmarks como MATH. Permanecem limitados pela incapacidade intrínseca de garantir exatidão sem chamada a ferramentas externas.

### 1.2. Abordagens Neuro-Simbólicas e Síntese de Programas
- **AlphaGeometry e AlphaGeometry 2 (Trinh et al., Nature 2024)**: Combina um modelo de linguagem que sugere construções geométricas auxiliares com um motor dedutivo simbólico baseado em álgebra de ângulos e áreas. Essa divisão — o LLM como gerador heurístico e o motor simbólico como verificador formal — inspira diretamente a filosofia do AXIOM. Diferencial do AXIOM: O AXIOM atua de forma multipropósito em múltiplos ramos da matemática (álgebra, cálculo, EDOs, tensores, teoria dos números, matrizes) e integra o kernel de tipos dependentes do Lean 4.
- **FunSearch (Romera-Paredes et al., Nature 2024)**: Utiliza LLMs para evoluir algoritmos em código Python, avaliados e ranqueados por um ambiente determinístico para problemas combinatórios abertos (como o problema do conjunto de cap). O AXIOM opera em direção análoga ao fornecer um ambiente com auditoria rigorosa de hipóteses e limites, garantindo que soluções propostas não violem restrições de domínio.

---

## 2. Ecossistema de Ferramentas MCP e Concorrentes

A análise detalhada em `docs/analise-concorrencia-mcp-2026.md` identifica os concorrentes diretos no ecossistema de Model Context Protocol:

### 2.1. Concorrente Direto: SymKit-MCP
O **SymKit-MCP** é o competidor mais próximo do AXIOM. Originado na linha neuro-simbólica do `nsforge-mcp`, foca em derivações simbólicas passo a passo com rastreamento completo de proveniência de fórmulas, suporte opcional a certificação Lean 4 e checagem de consistência dimensional.
- **Pontos Fortes do SymKit**: Forte modelagem de física e engenharia (análise dimensional estrita), grande suíte de testes em derivação algébrica.
- **Diferencial e Vantagem do AXIOM**: O AXIOM tem cobertura matemática substancialmente mais ampla (tensores de relatividade geral, teoria analítica dos números, geometria riemanniana, otimização e estatística multivariada), além de implementar **auditoria explícita de domínio e singularidades internas** (evitando que simplificações como $\frac{x-1}{x-1} \to 1$ ou $\sqrt{x^2} \to x$ passem desapercebidas).

### 2.2. Wrappers de Álgebra Computacional (CAS)
- **sdiehl/sympy-mcp**: Expõe funções brutas do SymPy ao agente. Retorna saídas sem verificação independente, sem contraexemplos numéricos e sem suporte a Lean 4.
- **abhiphile/fermat-mcp**: Combina SymPy, NumPy e Matplotlib em um servidor único. Funciona como calculadora multi-biblioteca: não verifica se o resultado numérico é uma aproximação ou exato e não detecta violações de restrições de domínio.
- **Wolfram 15 AgentTools & Wolfram MCP Oficial**: Disponibiliza o motor Wolfram Language e Wolfram|Alpha como servidor MCP local. Trata-se de um software proprietário, caixa-preta, sem verificação independente ortogonal e sem suporte nativo a prova formal com kernel aberto.

### 2.3. Ferramentas de Prova Formal (Lean 4)
- **project-numina/lean-lsp-mcp**: Expõe o Language Server Protocol (LSP) do Lean 4, inspecionando diagnósticos, goals e busca no Mathlib. É uma ferramenta especializada para redigir código Lean, carecendo de CAS, cálculo diferencial/integral, tensores e visualização.
- **KrystianYCSilva/lean-mcp**: Compila código Lean básico, mas não audita dependências axiomáticas via `#print axioms` nem bloqueia tautologias triviais (`rfl`).

---

## 3. Matriz Comparativa Científica

A tabela abaixo compara o AXIOM com as principais abordagens existentes:

| Capacidade | LLM Puro (e.g. GPT-4o / Claude 3.5) | CAS Puro / `sympy-mcp` | Wolfram MCP Oficial | `lean-lsp-mcp` | `symkit-mcp` | **Chronokairo AXIOM** |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Código aberto e reprodutível** | ❌ | ✅ | ❌ | ✅ | ✅ | **✅ (MIT)** |
| **Multidomínio (Álgebra, Cálculo, EDO, Tensores, Teoria dos Números)** | Heurístico | ✅ | ✅ | ❌ | Parcial (Fórmula/Física) | **✅ (Amplo)** |
| **Hierarquia estrita de garantias (`Guarantee`)** | ❌ | ❌ | ❌ | ❌ | Parcial | **✅ (6 níveis estritos)** |
| **Verificação independente e ortogonal** | ❌ | ❌ | ❌ | Kernel único | Simbólica/Dimensional | **✅ (Ortogonal: CAS + mpmath + Lean)** |
| **Preservação de restrições de domínio ($\frac{x-1}{x-1}$, $\sqrt{x^2}$)** | ❌ | ❌ | ❌ | ✅ (Tipos) | Parcial | **✅ (Sintático + Provas Gaussianas)** |
| **Comportamento fail-closed em singularidades e polos** | ❌ | ❌ | ❌ | N/A | ❌ | **✅ (Auditoria de Polos e Limites)** |
| **Prova Formal com auditoria de axiomas (`#print axioms`)** | ❌ | ❌ | ❌ | Manual | Opcional | **✅ (Automática e fail-closed)** |
| **Detecção de tautologias reflexivas triviais (`rfl`)** | ❌ | ❌ | ❌ | ❌ | ❌ | **✅ (Lema não trivial exigido)** |
| **Sessão persistente e exportação de relatórios científicos** | ❌ | ❌ | ✅ | ❌ | ✅ | **✅ (Markdown / JSON)** |

---

## 4. Conclusão do Posicionamento

O AXIOM preenche uma lacuna fundamental na literatura de inteligência artificial matemática: não tenta ser um LLM matemático nem apenas mais um wrapper de CAS. Ele atua como uma **camada de integridade epistemológica (Epistemic Integrity Layer)**, garantindo que qualquer declaração originada de um agente ou motor seja submetida a contratos estritos, auditorias de hipóteses de domínio e contraprovas automatizadas antes de ser aceita.
