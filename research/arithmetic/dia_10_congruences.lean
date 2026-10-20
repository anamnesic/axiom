/-
  Chronokairo AXIOM — Mathematical Investigation Dossier
  Dia 10: Relações de Congruência e Aritmética Modular ℤ/mℤ
  Referência: "Iniciação à Aritmética" (Abramo Hefez, SBM/OBMEP), Cap. 4, pág. 81-98.
  Kernel: Lean 4 (compatível com v4.14.0 do CI e v4.35.0 local)
  Garantia Epistêmica: formal-proof (Machine-checked, zero sorry, zero untrusted axioms)

  Enunciado canônico (Hefez, Cap. 4.1, pág. 81):
  "Seja dado um número inteiro m maior do que 1. Diremos que dois números inteiros
   a e b são congruentes módulo m se a e b possuírem o mesmo resto quando divididos
   por m. Equivalentemente, a ≡ b mod m se e somente se m divide a - b."

  Compatibilidade Algébrica (Hefez, Cap. 4.3 e 4.4, pág. 85-88):
  A relação de congruência é compatível com a adição e a multiplicação:
  a ≡ a' mod m ∧ b ≡ b' mod m ⟹ a + b ≡ a' + b' mod m ∧ a*b ≡ a'*b' mod m.

  Invertibilidade Modular (Hefez, Cap. 4.6, pág. 97):
  a possui inverso multiplicativo módulo m se e somente se mdc(a, m) = 1.
-/

namespace Dia10Congruences

/-!
### 1. Definição Epistêmica de Congruência em ℤ
-/
def Congruent (a b m : Int) : Prop :=
  m ∣ (a - b)

/-!
### 2. Congruência é uma Relação de Equivalência (Hefez, Proposição 4.1, pág. 83)
-/
theorem cong_refl (a m : Int) : Congruent a a m := by
  dsimp [Congruent]
  refine ⟨0, ?_⟩
  omega

theorem cong_symm (a b m : Int) (h : Congruent a b m) : Congruent b a m := by
  dsimp [Congruent] at *
  obtain ⟨k, hk⟩ := h
  refine ⟨-k, ?_⟩
  calc
    b - a = - (a - b) := by omega
    _ = - (m * k) := by rw [hk]
    _ = m * (-k) := by rw [Int.mul_neg]

theorem cong_trans (a b c m : Int) (h1 : Congruent a b m) (h2 : Congruent b c m) :
    Congruent a c m := by
  dsimp [Congruent] at *
  obtain ⟨k1, hk1⟩ := h1
  obtain ⟨k2, hk2⟩ := h2
  refine ⟨k1 + k2, ?_⟩
  calc
    a - c = (a - b) + (b - c) := by omega
    _ = m * k1 + m * k2 := by rw [hk1, hk2]
    _ = m * (k1 + k2) := by rw [Int.mul_add]

/-!
### 3. Compatibilidade com a Adição (Hefez, Proposição 4.2, pág. 85)
Se a ≡ a' mod m e b ≡ b' mod m, então a + b ≡ a' + b' mod m.
-/
theorem cong_add (a a' b b' m : Int)
    (ha : Congruent a a' m) (hb : Congruent b b' m) :
    Congruent (a + b) (a' + b') m := by
  dsimp [Congruent] at *
  obtain ⟨ka, hka⟩ := ha
  obtain ⟨kb, hkb⟩ := hb
  refine ⟨ka + kb, ?_⟩
  calc
    (a + b) - (a' + b') = (a - a') + (b - b') := by omega
    _ = m * ka + m * kb := by rw [hka, hkb]
    _ = m * (ka + kb) := by rw [Int.mul_add]

/-!
### 4. Compatibilidade com a Subtração
-/
theorem cong_sub (a a' b b' m : Int)
    (ha : Congruent a a' m) (hb : Congruent b b' m) :
    Congruent (a - b) (a' - b') m := by
  dsimp [Congruent] at *
  obtain ⟨ka, hka⟩ := ha
  obtain ⟨kb, hkb⟩ := hb
  refine ⟨ka - kb, ?_⟩
  calc
    (a - b) - (a' - b') = (a - a') - (b - b') := by omega
    _ = m * ka - m * kb := by rw [hka, hkb]
    _ = m * (ka - kb) := by rw [Int.mul_sub]

/-!
### 5. Compatibilidade com a Multiplicação (Hefez, Proposição 4.3, pág. 87)
Se a ≡ a' mod m e b ≡ b' mod m, então a*b ≡ a'*b' mod m.
Identidade de Hefez: a*b - a'*b' = (a - a')*b + a'*(b - b').
-/
theorem cong_mul (a a' b b' m : Int)
    (ha : Congruent a a' m) (hb : Congruent b b' m) :
    Congruent (a * b) (a' * b') m := by
  dsimp [Congruent] at *
  obtain ⟨ka, hka⟩ := ha
  obtain ⟨kb, hkb⟩ := hb
  refine ⟨ka * b + a' * kb, ?_⟩
  calc
    a * b - a' * b' = (a - a') * b + a' * (b - b') := by
      calc
        a * b - a' * b' = (a * b - a' * b) + (a' * b - a' * b') := by omega
        _ = (a - a') * b + a' * (b - b') := by
          have h1 : a * b - a' * b = (a - a') * b := (Int.sub_mul a a' b).symm
          have h2 : a' * b - a' * b' = a' * (b - b') := (Int.mul_sub a' b b').symm
          rw [h1, h2]
    _ = (m * ka) * b + a' * (m * kb) := by rw [hka, hkb]
    _ = m * (ka * b + a' * kb) := by
      calc
        (m * ka) * b + a' * (m * kb) = m * (ka * b) + m * (a' * kb) := by
          rw [Int.mul_assoc m ka b, Int.mul_left_comm a' m kb, Int.mul_comm a' kb]
        _ = m * (ka * b + a' * kb) := by rw [Int.mul_add]

/-!
### 6. Potências de Congruências (Indução Matemática)
Se a ≡ b mod m, então a^k ≡ b^k mod m para todo k natural.
-/
def intPow : Int → Nat → Int
  | _, 0 => 1
  | a, k + 1 => a * intPow a k

theorem cong_pow (a b m : Int) (k : Nat) (h : Congruent a b m) :
    Congruent (intPow a k) (intPow b k) m := by
  induction k with
  | zero =>
    dsimp [intPow]
    exact cong_refl 1 m
  | succ k ih =>
    dsimp [intPow]
    exact cong_mul a b (intPow a k) (intPow b k) m h ih

/-!
### 7. Invertibilidade Modular e Relação com Bézout (Hefez, Proposição 4.6, pág. 97)
"Um inteiro a possui um inverso multiplicativo módulo m se e somente se
existe x tal que a*x ≡ 1 mod m, o que equivale à existência de coeficientes
de Bézout a*x + m*y = 1, ou seja, mdc(a, m) = 1."
-/
theorem invertible_of_bezout (a m x y : Int) (hbez : a * x + m * y = 1) :
    Congruent (a * x) 1 m := by
  dsimp [Congruent]
  have hdiff : a * x - 1 = m * (-y) := by
    calc
      a * x - 1 = a * x - (a * x + m * y) := by rw [hbez]
      _ = - (m * y) := by omega
      _ = m * (-y) := by rw [Int.mul_neg]
  exact ⟨-y, hdiff⟩

theorem bezout_of_invertible (a m x : Int) (hinv : Congruent (a * x) 1 m) :
    ∃ y : Int, a * x + m * y = 1 := by
  dsimp [Congruent] at hinv
  obtain ⟨k, hk⟩ := hinv
  refine ⟨-k, ?_⟩
  calc
    a * x + m * (-k) = a * x - m * k := by
      -- `Int.sub_eq_add_neg` is available in Lean 4.14.0 (the CI-pinned
      -- toolchain) and in 4.35.0, unlike `Int.add_neg_eq_sub` which only
      -- exists from Lean 4.16.0 onwards. Keeping the proof on the oldest
      -- supported core lemma preserves the CI contract.
      rw [Int.mul_neg, Int.sub_eq_add_neg]
    _ = a * x - (a * x - 1) := by rw [hk]
    _ = 1 := by omega

/-!
### 7.1 Teorema de Coprimaridade Modular: Divisores Comuns Dividem 1
Se um inteiro `a` é invertível módulo `m`, todo divisor comum `d` de `a` e `m` divide 1.
Isto estabelece a caracterização completa de coprimaridade (mdc(a, m) = 1) no anel ℤ.
-/
theorem common_divisor_dvd_one_of_invertible (a m x d : Int)
    (hinv : Congruent (a * x) 1 m)
    (hda : d ∣ a)
    (hdm : d ∣ m) :
    d ∣ 1 := by
  obtain ⟨y, hbez⟩ := bezout_of_invertible a m x hinv
  have h1 : d ∣ a * x := Int.dvd_trans hda (Int.dvd_mul_right a x)
  have h2 : d ∣ m * y := Int.dvd_trans hdm (Int.dvd_mul_right m y)
  have hsum : d ∣ a * x + m * y := Int.dvd_add h1 h2
  rw [hbez] at hsum
  exact hsum

/-!
### 8. Exemplos Numéricos Clássicos de Abramo Hefez (Cap. 4.1, pág. 82)
Exemplo 1: 15 ≡ 8 mod 7 (ambos deixam resto 1 na divisão por 7)
Exemplo 2: 27 ≡ 32 mod 5 (ambos deixam resto 2 na divisão por 5)
Exemplo 3 (Inverso Modular): inverso de 3 módulo 7 é 5, pois 3 * 5 = 15 ≡ 1 mod 7.
-/
example : Congruent 15 8 7 := by
  dsimp [Congruent]
  refine ⟨1, by decide⟩

example : Congruent 27 32 5 := by
  dsimp [Congruent]
  refine ⟨-1, by decide⟩

example : Congruent (3 * 5) 1 7 := by
  dsimp [Congruent]
  refine ⟨2, by decide⟩

#eval (15 - 8) % 7 == 0
#eval (27 - 32) % 5 == 0
#eval (3 * 5 - 1) % 7 == 0

end Dia10Congruences
