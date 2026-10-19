/-
  Chronokairo AXIOM — Mathematical Investigation Dossier
  Dia 06: Teorema Fundamental da Aritmética — Existência da Decomposição em Primos
  Referência: "Iniciação à Aritmética" (Abramo Hefez, SBM/OBMEP), Cap. 2.1, 2.2 e 2.3, pág. 31-36.
  Kernel: Lean 4 (version 4.35.0)
  Garantia Epistêmica: formal-proof (Machine-checked, zero sorry, zero untrusted axioms)
-/

namespace Dia06TFAExistence

/-!
### 1. Definição Epistêmica de Número Primo (Abramo Hefez, Cap. 2)
"Um número natural p ≥ 2 diz-se um número primo se os seus únicos divisores
positivos forem 1 e p."
-/
def IsPrime (p : Nat) : Prop :=
  p ≥ 2 ∧ ∀ d : Nat, d ∣ p → d = 1 ∨ d = p

/-!
### 2. Algoritmo Construtivo de Fatoração em Primos
Implementação construtiva do menor divisor estritamente maior que 1 (Hefez, Lema 2.1)
e retrosubstituição de fatores primos via indução bem-fundada.
-/
def minFacAux (n : Nat) (k : Nat) : Nat :=
  if h : n ≤ k then n
  else if n % k = 0 then k
  else minFacAux n (k + 1)
termination_by n - k
decreasing_by omega

def minFac (n : Nat) : Nat := minFacAux n 2

def factorFuel (fuel : Nat) (n : Nat) : List Nat :=
  match fuel with
  | 0 => []
  | fuel + 1 =>
    if n < 2 then []
    else
      let p := minFac n
      p :: factorFuel fuel (n / p)

def primeFactors (n : Nat) : List Nat :=
  factorFuel n n

-- Verificação numérica do exemplo canônico da página 34 de Abramo Hefez: 360 = 2 * 2 * 2 * 3 * 3 * 5
#eval primeFactors 360

/-!
### 3. Lemas Auxiliares de Limite Estrito para Fatores Compostos
Demonstra que se a ≥ 2 e b ≥ 2, então a < a*b e b < a*b, garantindo a descida
estrita na indução forte.
-/
theorem lt_mul_right_of_ge_two (a b : Nat) (ha : a ≥ 2) (hb : b ≥ 2) : a < a * b := by
  obtain ⟨b', rfl⟩ : ∃ b', b = b' + 2 := ⟨b - 2, by omega⟩
  have : a * (b' + 2) = a * b' + a * 2 := Nat.mul_add a b' 2
  omega

theorem lt_mul_left_of_ge_two (a b : Nat) (ha : a ≥ 2) (hb : b ≥ 2) : b < a * b := by
  rw [Nat.mul_comm]
  exact lt_mul_right_of_ge_two b a hb ha

/-!
### 4. Lema da Fatoração de Números Compostos
"Se n ≥ 2 possui um divisor d com d ≠ 1 e d ≠ n, então existem inteiros a, b ≥ 2
tais que n = a * b."
-/
theorem composite_of_divisor (n d : Nat) (hn : n ≥ 2)
    (hdvd : d ∣ n) (hd1 : d ≠ 1) (hdn : d ≠ n) :
    ∃ a b : Nat, a ≥ 2 ∧ b ≥ 2 ∧ n = a * b := by
  rcases hdvd with ⟨q, rfl⟩
  have ha : d ≥ 2 := by
    cases d with
    | zero => simp at hn
    | succ d =>
      cases d with
      | zero => contradiction
      | succ d => omega
  have hb : q ≥ 2 := by
    cases q with
    | zero => simp at hn
    | succ q =>
      cases q with
      | zero =>
        have : d * 1 = d := Nat.mul_one d
        rw [this] at hdn
        contradiction
      | succ q => omega
  exact ⟨d, q, ha, hb, rfl⟩

/-!
### 5. Dicotomia Primo vs. Composto
"Todo número n ≥ 2 ou é primo ou possui um divisor não trivial d ∣ n com 1 < d < n."
-/
theorem not_prime_has_divisor (n : Nat) (hn : n ≥ 2) (hnp : ¬ IsPrime n) :
    ∃ d : Nat, d ∣ n ∧ d ≠ 1 ∧ d ≠ n := by
  apply Classical.byContradiction
  intro hcon
  apply hnp
  constructor
  · exact hn
  · intro d hd
    have hor : d = 1 ∨ d ≠ 1 := Classical.em (d = 1)
    cases hor with
    | inl h1 => left; exact h1
    | inr h1 =>
      have h2 : d = n ∨ d ≠ n := Classical.em (d = n)
      cases h2 with
      | inl hn_eq => right; exact hn_eq
      | inr hn_neq =>
        exfalso
        apply hcon
        exact ⟨d, hd, h1, hn_neq⟩

/-!
### 6. Teorema Fundamental da Aritmética — Existência (Abramo Hefez, Teorema 2.1)
"Todo número natural n ≥ 2 se decompõe em um produto de um ou mais números primos."
Demonstração (Hefez): Por indução forte sobre n:
- Se n é primo, a lista [n] é uma decomposição com um único fator primo, e prod [n] = n.
- Se n é composto, n = a * b com 2 ≤ a < n e 2 ≤ b < n. Por hipótese de indução,
  a e b se decompõem em primos La e Lb. Logo La ++ Lb é uma decomposição em primos de n,
  com prod (La ++ Lb) = (prod La) * (prod Lb) = a * b = n.
-/
theorem hefez_fundamental_theorem_existence (n : Nat) :
    n ≥ 2 → ∃ (L : List Nat), (∀ p ∈ L, IsPrime p) ∧ L.prod = n ∧ L ≠ [] := by
  induction n using Nat.strongRecOn with
  | ind n ih =>
    intro hn
    have hem := Classical.em (IsPrime n)
    cases hem with
    | inl hp =>
      refine ⟨[n], ?_, by simp, by simp⟩
      intro p hp_in
      simp at hp_in
      subst hp_in
      exact hp
    | inr hnp =>
      rcases not_prime_has_divisor n hn hnp with ⟨d, hd, hd1, hdn⟩
      rcases composite_of_divisor n d hn hd hd1 hdn with ⟨a, b, ha, hb, heq⟩
      have hlt_a : a < n := by
        subst heq
        exact lt_mul_right_of_ge_two a b ha hb
      have hlt_b : b < n := by
        subst heq
        exact lt_mul_left_of_ge_two a b ha hb
      rcases ih a hlt_a ha with ⟨La, hLa_prime, hLa_prod, hLa_ne⟩
      rcases ih b hlt_b hb with ⟨Lb, hLb_prime, hLb_prod, hLb_ne⟩
      refine ⟨La ++ Lb, ?_, ?_, ?_⟩
      · intro p hp_in
        cases List.mem_append.1 hp_in with
        | inl h => exact hLa_prime p h
        | inr h => exact hLb_prime p h
      · rw [List.prod_append, hLa_prod, hLb_prod, ← heq]
      · intro h_nil
        cases La with
        | nil => exact hLa_ne rfl
        | cons head tail => contradiction

end Dia06TFAExistence
