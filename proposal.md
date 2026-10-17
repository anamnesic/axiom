# Proposta de Pesquisa: Arquitetura Neuro-Simbólica com Verificação Independente e Integridade de Domínio

**Projeto**: Chronokairo AXIOM (Mathematical Reasoning Engine)  
**Data**: 17 de outubro de 2026  
**Autoria**: Chronokairo  
**Área**: Ciência da Computação / Matemática Computacional / Inteligência Artificial Neuro-Simbólica  

---

## 1. Contexto e Delimitação do Problema

Modelos de Linguagem de Grande Escala (LLMs) demonstraram capacidade expressiva no raciocínio matemático informal (e.g., GSM8K, MATH, Olimpíadas Internacionais de Matemática). Contudo, quando inseridos em laços autônomos de agentes (Agentic AI loops), os LLMs sofrem de três patologias fundamentais:

1. **Alucinação Aritmética e Algébrica**: LLMs geram derivações estruturalmente convincentes, mas com passos intermediários inválidos ou falsas simplificações.
2. **Perda Silenciosa de Restrições de Domínio**: Sistemas convencionais de álgebra computacional (CAS) como SymPy e Mathematica frequentemente simplificam frações como $\frac{x-1}{x-1} \to 1$ de forma irrestrita, perdendo a informação crítica de que $x \neq 1$, o que conduz a raízes espúrias e divisões por zero mascaradas.
3. **Opacidade Probatória e Ausência de Contratos de Evidência**: A grande maioria das ferramentas MCP (Model Context Protocol) disponíveis conecta agentes a CAS brutos (e.g., `sympy-mcp`, `fermat-mcp`), devolvendo strings sem metadados de reprodutibilidade, sem dupla checagem numérica e sem capacidade de auditoria por provadores formais (como o Lean 4).

## 2. Pergunta Central de Pesquisa

> **Como estruturar uma interface unificada e neuro-simbólica (via Model Context Protocol) entre agentes de IA, motores de álgebra computacional e assistentes de prova formal, de modo que cada operação matemática seja acompanhada por evidências reproduzíveis e uma garantia hierárquica fail-closed que preserve a integridade do domínio algébrico?**

---

## 3. Hipótese Científica

Uma arquitetura de raciocínio matemático baseada em:
1. **Parsing estrito com retenção de restrições de domínio** antes da simplificação avaliativa;
2. **Verificação independente e ortogonal** (onde o verificador utiliza um método distinto do motor que produziu a resposta);
3. **Contrato de evidência com hierarquia estrita de garantias** (`formal-proof` $\succ$ `exact-symbolic` $\succ$ `verified-substitution` $\succ$ `numerical-approximation` $\succ$ `heuristic` $\succ$ `unverified`);
4. **Comportamento fail-closed perante singularidades e divergências**;

é capaz de **eliminar 100% das falsas equivalências por branch cut e singularidade** em benchmarks de álgebra e cálculo em comparação com LLMs isolados e wrappers simples de CAS, mantendo latência compatível com laços interativos de agentes.

---

## 4. Objetivos

### 4.1. Objetivo Geral
Desenvolver, formalizar e validar experimentalmente o **AXIOM**, um motor neuro-simbólico de raciocínio matemático para agentes autônomos, implementado como servidor MCP de alto desempenho e CLI determinística.

### 4.2. Objetivos Específicos
1. **Formalizar o Contrato AXIOM (`MathResult`)**: Definir a estrutura matemática de dados com campos obrigatórios (`ok`, `value`, `guarantee`, `evidence`, `verification`, `limitations`), garantindo que nenhuma afirmação matemática receba garantia sem um objeto `Verification` aprovado.
2. **Implementar a Auditoria de Domínio e Hipóteses**: Construir um parser AST com allowlist que rastreie denominadores originais antes da simplificação do SymPy e imponha amostragem complexa gaussiana para refutar identidades inválidas em $\mathbb{C}$.
3. **Integrar Prova Formal no Loop de Execução**: Conectar o kernel do Lean 4 e o Mathlib4, estabelecendo um auditor de axiomas que rejeite provas com `sorry`, axiomas de usuário não-confiáveis ou tautologias reflexivas triviais (`rfl`).
4. **Estabelecer Benchmarks de Verificação**: Construir uma suíte quantitativa de testes com problemas de fronteira de domínio, limites bilaterais descontínuos, integrais de singularidade interna e problemas do Millennium.

---

## 5. Metodologia de Pesquisa

A pesquisa segue o método de engenharia de sistemas rigorosos orientada a evidências (*Evidence-Based Software & Mathematical Engineering*):
- **Ciclo de Desenvolvimento**: Implementação em Python 3.10–3.14 com tipagem estrita (`mypy`), suíte abrangente de testes (`pytest` e `unittest`) e integração contínua (CI) multiplataforma (Ubuntu, Windows, macOS).
- **Verificação Ortogonal**:
  - Operações de álgebra e limites são conferidas por amostragem numérica em aritmética de multiprecisão (`mpmath`).
  - Derivadas são checadas por diferenças finitas centrais de alta precisão.
  - Integrais são verificadas por diferenciação da antiderivada e quadratura adaptativa de Gauss-Legendre.
  - Soluções de equações são validadas por substituição direta e auditoria de raízes estranhas.
  - Teoremas formais são checados pelo kernel do Lean 4 via comando Lake.
- **Validação Empírica em Problemas em Aberto**: Aplicação em instâncias canônicas dos Problemas do Millennium (P vs NP, Hipótese de Riemann, etc.) para testar limites de decidibilidade e comportamento fail-closed.

---

## 6. Resultados Esperados e Impacto

1. **Repositório e Pacote Aberto**: Disponibilização do AXIOM sob licença MIT no GitHub e PyPI como infraestrutura de referência para ferramentas matemáticas MCP.
2. **Publicação Acadêmica**: Artigo científico documentando a arquitetura, a hierarquia de garantias e os resultados quantitativos de integridade de domínio perante modelos de fronteira (Claude 3.5, GPT-4o, Gemini 1.5/2.0).
3. **Padrão de Interoperabilidade para Agentes**: Especificação do padrão de evidências matemáticas reproduzíveis para AI Coding Agents (Claude Code, Cursor, Codex, Gemini CLI).
