# Reproducible Arithmetic Corpus (Lean 4)

Este diretório contém o corpus formal versionado de provas matemáticas em **Lean 4**, derivadas da formalização e investigação da obra *"Iniciação à Aritmética"* (Abramo Hefez, SBM/OBMEP), acompanhando o desenvolvimento do **Chronokairo AXIOM**.

Diferente de artefatos efêmeros gerados em `build/`, os arquivos contidos aqui são **fontes canônicas rastreadas pelo Git**, permitindo que auditores e a suíte de Integração Contínua (CI) reproduzam e certifiquem cada teorema com zero axiomas espúrios.

---

## 📚 Índice de Demonstrações Formais

| Arquivo | Tópico Formal | Referência Hefez | Status Epistêmico |
| :--- | :--- | :--- | :--- |
| [`HefezTheorems.lean`](./HefezTheorems.lean) | Fundamentos de divisibilidade, boa-ordenação e algoritmo da divisão | Cap. 1 & 2 | Machine-checked (0 sorry) |
| [`dia_04_bezout.lean`](./dia_04_bezout.lean) | Identidade de Bézout e Algoritmo Estendido de Euclides (XGCD) | Seções 3.8 / 3.9 (p. 66–74) | Machine-checked (0 sorry) |
| [`dia_05_euclid_lemma.lean`](./dia_05_euclid_lemma.lean) | Coprimalidade e Lema de Euclides ($p \mid ab \implies p \mid a \lor p \mid b$) | Seção 3.5 & Teorema 3.4 | Machine-checked (0 sorry) |
| [`dia_06_fundamental_theorem_existence.lean`](./dia_06_fundamental_theorem_existence.lean) | Teorema Fundamental da Aritmética: **Existência** da fatoração prima | Seção 2.1–2.3 & Lema 2.1 | Machine-checked (0 sorry) |
| [`dia_07_fundamental_theorem_uniqueness.lean`](./dia_07_fundamental_theorem_uniqueness.lean) | Teorema Fundamental da Aritmética: **Unicidade** da fatoração prima | Teorema 3.5 & Corolário 3.6 | Machine-checked (0 sorry) |
| [`dia_08_euclid_infinitude.lean`](./dia_08_euclid_infinitude.lean) | Teorema de Euclides: **Infinitude** dos números primos ($\forall n, \exists p > n$) | Seção 2.4 (p. 40) & Problema 1.21 | Machine-checked (0 sorry) |
| [`dia_09_diophantine.lean`](./dia_09_diophantine.lean) | Equações Diofantinas Lineares: Critério e Solução Geral ($ax + by = c$) | Seção 3.10 (p. 75–80, Teorema 3.5) | Machine-checked (0 sorry) |
| [`dia_10_congruences.lean`](./dia_10_congruences.lean) | Relações de Congruência, Aritmética Modular e Inverso via Bézout | Cap. 4 (p. 81–98, Proposições 4.1–4.6) | Machine-checked (0 sorry) |
| [`dia_11_fermat.lean`](./dia_11_fermat.lean) | Pequeno Teorema de Fermat (Formas Aditiva e Multiplicativa) | Brochero et al., Cap. 3; Hefez, Cap. 4 | Machine-checked (0 sorry) |
| [`dia_12_wilson.lean`](./dia_12_wilson.lean) | Wilson: $p \ge 2 \implies (p \text{ primo} \iff p \mid (p-1)!+1)$ | Brochero et al., §1.6, Teorema 1.34, p. 44 | `formal-proof` (31 teoremas, 0 sorry) |

---

## 🛡️ Garantias Epistêmicas

1. **Kernel Oficial Lean 4**: Todas as provas compilam com o kernel Lean 4 (dualmente compatível com leanprover/lean4:v4.14.0 do CI e leanprover/lean4:v4.35.0 local).
2. **Zero `sorry`**: Nenhuma demonstração recorre a passos incompletos.
3. **Zero axiomas não-confiáveis**: Verificado via inspeção de axiomas (nenhum axioma ad-hoc introduzido).
4. **Independência de Mathlib**: Todas as formalizações foram construídas de forma autossuficiente sobre o núcleo do Lean 4 e a tática `omega`, eliminando fragilidades de dependências externas.
5. **Algoritmos Construtivos e Verificação Simbólica**: Inclui implementações executáveis `#eval` para instâncias numéricas históricas (e.g., Bézout para 372 e 162, fatoração canônica de 360).

---

## 🚀 Como Reproduzir

### 1. Diretamente via Lean 4 CLI
Com o Lean 4 instalado via `elan`:
```bash
lean research/arithmetic/dia_04_bezout.lean
lean research/arithmetic/dia_05_euclid_lemma.lean
lean research/arithmetic/dia_06_fundamental_theorem_existence.lean
lean research/arithmetic/dia_07_fundamental_theorem_uniqueness.lean
lean research/arithmetic/dia_08_euclid_infinitude.lean
lean research/arithmetic/dia_09_diophantine.lean
lean research/arithmetic/dia_10_congruences.lean
lean research/arithmetic/dia_11_fermat.lean
lean research/arithmetic/dia_12_wilson.lean
```

### 2. Pelo Chronokairo AXIOM
Você pode carregar e auditar as provas formalizadas dentro de uma sessão científica do AXIOM:
```python
from axiom import Axiom

ax = Axiom()
res = ax.verify_lean_file("research/arithmetic/dia_06_fundamental_theorem_existence.lean")
print(res.epistemic_state, res.verified, res.guarantee)
```

### 3. Na Integração Contínua (CI)
O job `formal-lean` em `.github/workflows/ci.yml` executa a checagem formal automatizada de todos os arquivos `.lean` deste diretório em cada push e pull request.

---

## 🏛️ Registros de Decisão Arquitetural (ADRs)
- [ADR-0023: Constructive Definition Tracking in Lean 4, LEAN_PATH Injection & Number Theory Expansion](../../docs/adr/0023-constructive-definition-tracking-lean-path-and-number-theory-expansion.md)
- [ADR-0024: Number Theory Payload Re-Verification in Sessions & Fundamental Theorem of Arithmetic (Existence)](../../docs/adr/0024-number-theory-payload-reverification-and-fundamental-arithmetic-existence.md)
- [ADR-0025: Payload Re-Verification Completeness, Proof Timeout Control, Metaprogramming Linter & Multiset Factors](../../docs/adr/0025-payload-reverification-completeness-timeout-linter-and-multiset-factors.md)
- [ADR-0026: CI Recovery, Tamper-Resistant Revalidation, Imported Hypothesis Downgrading & Versioned Arithmetic Corpus](../../docs/adr/0026-ci-recovery-tamper-detection-and-versioned-arithmetic-corpus.md)
