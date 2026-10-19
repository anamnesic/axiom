# ADR-0023: Rastreamento de Definições Construtivas no Lean 4, Injeção de LEAN_PATH e Expansão da Aritmética Computacional

**Status:** Aceito  
**Data:** 19 de Outubro de 2026  
**Contexto:** Investigação Matemática Contínua (Transição do Dia 05 para o Dia 06 do Currículo de Aritmética)

---

## 1. Contexto e Motivação

Durante as investigações formais dos Dias 04 e 05 (*Iniciação à Aritmética*, Abramo Hefez), dois requisitos técnicos centrais surgiram:

1. **Rastreamento de Definições Construtivas (`def`):**
   Modelos matemáticos rigorosos e algoritmos fundamentais (como `xgcd` no Dia 04 e `IsPrime` no Dia 05) são introduzidos via `def` e não via `theorem`. No entanto, o `LeanEngine` do AXIOM focava exclusivamente em extrair teoremas para `#print axioms`, ignorando definições em sua resposta estruturada (`Answer.value`). Isso deixava agentes de IA sem visibilidade sobre os predicados e construtos algorítmicos introduzidos.

2. **Isolamento de Arquivos e Dependências Modulares (`LEAN_PATH`):**
   O sandbox do `LeanEngine` não configurava o `LEAN_PATH` com o diretório do arquivo sob teste (`origin_path.parent`), impossibilitando importações de módulos auxiliares compilados na mesma pasta sem um Lakefile completo.

3. **Primitivas Computacionais de Teoria dos Números para os Dias 06 a 08:**
   O Teorema Fundamental da Aritmética (Fatoração em Primos, Dias 06 e 07) e o Teorema de Euclides sobre a Infinitude dos Primos (Dia 08) exigem a enumeração exata e verificação de listas completas de divisores próprios e fatores primos irredutíveis.

---

## 2. Decisões Arquiteturais

### D1: Analisador de Escopo e Rastreamento de Definições Construtivas (`LeanEngine.extract_definitions`)
- Implementamos `LeanEngine.extract_definitions(source: str) -> list[str]`.
- O analisador rastreia a pilha lexical de `namespace` e `section`, retornando identificadores totalmente qualificados (ex: `Dia05EuclidLemma.IsPrime`, `Dia04Bezout.xgcd`).
- O retorno estruturado do `LeanEngine` (`Answer.value` e `Answer.raw`) agora inclui o campo `"definitions": list[str]`.
- Se um arquivo contiver apenas definições sem teoremas, o sistema emite um aviso informativo detalhado em vez de rejeição opaca.

### D2: Injeção de Diretório de Origem no `LEAN_PATH` do Ambiente Isolado
- O método `_build_sandboxed_env` passa a receber `origin_path: Path | None = None`.
- Se `origin_path` existir, seu diretório pai é resolvido e automaticamente incluído em `env["LEAN_PATH"]`, viabilizando importações de artefatos `.olean` e módulos irmãos.

### D3: Novas Operações de Teoria dos Números (`divisors` e `primefactors`)
- Em `src/axiom/engines/sympy_engine.py`:
  - `divisors`: enumera todos os divisores inteiros positivos de $n \ge 1$ via `sympy.divisors`.
  - `primefactors`: enumera o conjunto ordenado dos fatores primos distintos de $n \ge 2$ via `sympy.primefactors`.
- Em `src/axiom/verification.py` (`verify_number_theory_op`):
  - `divisors`: verifica duplamente a divisibilidade de cada elemento, a presença de $1$ e $n$, o emparelhamento complementar ($d \implies n/d$) e verificação exaustiva até $10^4$.
  - `primefactors`: audita a primalidade de cada fator, confirma que divide $n$ e verifica a exaustão total de $n$ por divisões sucessivas.
- Em `src/axiom/cli.py`:
  - `axiom number-theory divisors -n <val>`
  - `axiom number-theory primefactors -n <val>`

---

## 3. Consequências e Benefícios

- **Visibilidade de Algoritmos e Predicados:** Provas que definem predicados e funções agora têm seus identificadores catalogados com precisão.
- **Preparação Completa para o TFA (Dias 06-08):** O AXIOM agora dispõe de motores formais e computacionais independentes para verificar fatorações e listas de divisores em tempo real.
- **Manutenção de 100% dos Testes de Regressão:** Todos os testes existentes e novos testes unitários passam de forma síncrona com certificação `VERIFIED_SUBSTITUTION`.
