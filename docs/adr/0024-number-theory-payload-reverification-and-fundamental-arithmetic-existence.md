# ADR 0024: Revalidação de Payloads de Teoria dos Números em Sessões e Formalização da Existência da Fatoração em Primos (TFA)

- **Status:** Accepted
- **Data:** 2026-10-19
- **Autores:** Chronokairo AXIOM Core Team & Antigravity Agent

---

## 1. Contexto e Motivação

Durante a formalização do **Dia 06** do plano de verificação matemática (*Iniciação à Aritmética*, Abramo Hefez, Cap. 2.1–2.3: Teorema Fundamental da Aritmética — Existência da Decomposição em Fatores Primos), formalizamos o teorema em Lean 4 com 0 `sorry` e integramos passos de validação computacional via `ax.number_theory("factorint", n=360)` e `ax.number_theory("primefactors", n=360)` na sessão de pesquisa `dia-06-tfa-existence`.

Contudo, ao consultar o status da sessão via `ax.session("status")`, o mecanismo de segurança epistêmica do AXIOM (ADR-0008/ADR-0009) acionou `ResearchSession.revalidate_all()`, que invocou `axiom.verify(entry)`.
No método `Axiom._verify_dict_payload`, apenas `solve`, `simplify/factor/expand/evaluate`, `integrate` e `prove` estavam mapeados para revalidação local. Passos com `kind == "number_theory"` geravam o erro:
`unsupported result payload kind for re-verification: 'number_theory'`.
Isso marcava indevidamente os passos de teoria dos números como `step_valid=False` e `chain_valid=False`, invalidando o DAG estrutural da sessão.

## 2. Decisões de Arquitetura

### D1: Suporte a `kind == "number_theory"` em `_verify_dict_payload`
- No método `Axiom._verify_dict_payload(payload)` em `src/axiom/core.py`:
  - Detectamos entradas com `kind == "number_theory"` e `input`.
  - Extraímos o nome da operação e os argumentos (e.g. `factorint({'n': 360})`) via `re.match` e `ast.literal_eval`.
  - Re-executamos a operação através de `self.number_theory(op_name, **args_dict)`, que aciona a camada de verificação independente (`verify_number_theory_op`).
  - O resultado retornado possui `verified=True` e `guarantee=Guarantee.VERIFIED_SUBSTITUTION`, restabelecendo a validade local do passo (`step_valid=True`) e a integridade da cadeia de dependências (`chain_valid=True`).

### D2: Formalização Construtiva e Existencial do TFA (Dia 06)
- Em `build/book_investigation/dia_06_fundamental_theorem_existence.lean` (protegido em `build/`, ignorado pelo git):
  - Definimos o menor divisor primo `minFacAux` / `minFac` com recursão bem-fundada provada por terminação `termination_by n - k`.
  - Implementamos o gerador construtivo de fatores `factorFuel` e `primeFactors`, avaliado com sucesso no exemplo canônico de Hefez: `primeFactors 360 = [2, 2, 2, 3, 3, 5]`.
  - Provamos os lemas aritméticos de desigualdade estrita: `lt_mul_right_of_ge_two` e `lt_mul_left_of_ge_two`.
  - Provamos `composite_of_divisor` e `not_prime_has_divisor`.
  - Provamos formalmente o teorema principal `hefez_fundamental_theorem_existence`:
    $$\forall n \ge 2, \exists (L : \text{List } \mathbb{N}), (\forall p \in L, \text{IsPrime } p) \land L.\text{prod} = n \land L \ne []$$
    usando indução forte em $\mathbb{N}$ via `Nat.strongRecOn`.
  - A verificação pelo kernel do Lean 4 atestou 0 `sorry`, 5 teoremas e 5 definições sob os axiomas canônicos (`propext`, `Quot.sound`, `Classical.choice`).

## 3. Consequências e Garantias

- **Integridade Epistêmica:** Sessões de pesquisa com derivações híbridas (provas formais em Lean 4 e cálculos de teoria dos números em SymPy) agora são 100% revalidadas no host local sem perda de estado.
- **Princípio do Elo Mais Fraco:** A sessão `dia-06-tfa-existence` possui 3/3 passos válidos, cadeia estrutural íntegra (`chain_valid=True`), garantia de passo `formal-proof` no teorema e garantia de elo mais fraco `verified-substitution` no agregado.
- **Suíte de Testes:** Adicionado teste de regressão em `tests/test_axiom.py` cobrindo a gravação e revalidação de passos `number_theory` em sessões de pesquisa.
