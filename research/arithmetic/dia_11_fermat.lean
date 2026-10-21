/-
  Chronokairo AXIOM — Mathematical Investigation Dossier
  Dia 11: Pequeno Teorema de Fermat
  Referência: "Teoria dos Números: Um Passeio pelos Primos" (Brochero et al., Projeto Euclides / IMPA), Cap. 3;
              "Iniciação à Aritmética" (Abramo Hefez, SBM/OBMEP), Cap. 4.
  Kernel: Lean 4 (compatível com v4.14.0 do CI e v4.35.0 local)
  Garantia Epistêmica: formal-proof (Machine-checked, zero sorry, zero untrusted axioms)

  Enunciado canônico (Brochero, Cap. 3 / Teorema 3.3):
  1. Forma Aditiva Geral: Se p é um número primo, então para todo natural a,
     a^p ≡ a (mod p).
  2. Forma Multiplicativa Clássica: Se p é um número primo e mdc(a, p) = 1,
     então a^(p-1) ≡ 1 (mod p).
-/

import Init.Data.Nat.Basic
import Init.Data.Int.Basic

namespace Dia11Fermat

/-!
### 1. Definições Epistêmicas Fundamentais
-/
def IsPrime (p : Nat) : Prop :=
  p ≥ 2 ∧ ∀ d : Nat, d ∣ p → d = 1 ∨ d = p

def Congruent (a b m : Int) : Prop :=
  m ∣ (a - b)

theorem cong_refl (a m : Int) : Congruent a a m := by
  dsimp [Congruent]
  refine ⟨0, by omega⟩

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
### 2. Bézout e Lema de Coprimaridade (Hefez, Cap. 3 / Dia 05)
-/
theorem hefez_bezout_algebra (m t s q r : Int) :
    m * (t - s * q) + (m * q + r) * s = r * s + m * t := by
  have h1 : m * (t - s * q) = m * t - m * (s * q) := Int.mul_sub m t (s * q)
  have h2 : (m * q + r) * s = (m * q) * s + r * s := Int.add_mul (m * q) r s
  have h3 : m * (s * q) = (m * q) * s := by
    rw [Int.mul_assoc, Int.mul_comm s q, ← Int.mul_assoc]
  rw [h1, h2, h3]
  omega

theorem hefez_bezout_identity (a b : Nat) :
    ∃ (x y : Int), (a : Int) * x + (b : Int) * y = (Nat.gcd a b : Int) := by
  induction a, b using Nat.gcd.induction with
  | H0 n =>
    exists 0, 1
    simp [Nat.gcd_zero_left]
  | H1 m n hm ih =>
    cases ih with
    | intro s hs =>
      cases hs with
      | intro t hst =>
        exists (t - s * ((n / m : Nat) : Int)), s
        have heuc : (n : Int) = (m : Int) * ((n / m : Nat) : Int) + ((n % m : Nat) : Int) := by
          have h := (Nat.div_add_mod n m).symm
          exact congrArg Int.ofNat h
        have halg := hefez_bezout_algebra (m : Int) t s ((n / m : Nat) : Int) ((n % m : Nat) : Int)
        have hgcd : (Nat.gcd m n : Nat) = Nat.gcd (n % m) m := Nat.gcd_rec m n
        rw [heuc]
        rw [halg]
        rw [hst]
        exact congrArg Int.ofNat hgcd.symm

theorem hefez_coprime_dvd_mul_int (a b c x y : Int)
    (hbez : a * x + b * y = 1)
    (hdvd : a ∣ b * c) :
    a ∣ c := by
  have hid : c = a * (x * c) + (b * c) * y := by
    calc
      c = 1 * c := by rw [Int.one_mul]
      _ = (a * x + b * y) * c := by rw [hbez]
      _ = (a * x) * c + (b * y) * c := by rw [Int.add_mul]
      _ = a * (x * c) + (b * c) * y := by
        rw [Int.mul_assoc a x c, Int.mul_assoc b y c, Int.mul_comm y c, ← Int.mul_assoc b c y]
  rw [hid]
  have h1 : a ∣ a * (x * c) := Int.dvd_mul_right a (x * c)
  have h2 : a ∣ (b * c) * y := Int.dvd_trans hdvd (Int.dvd_mul_right (b * c) y)
  exact Int.dvd_add h1 h2

theorem hefez_prime_gcd_cases (p a : Nat) (hp : IsPrime p) :
    Nat.gcd p a = 1 ∨ Nat.gcd p a = p := by
  have hdvd : Nat.gcd p a ∣ p := Nat.gcd_dvd_left p a
  exact hp.2 (Nat.gcd p a) hdvd

theorem hefez_euclid_lemma (p a b : Nat)
    (hp : IsPrime p)
    (hdvd : p ∣ a * b) :
    p ∣ a ∨ p ∣ b := by
  cases hefez_prime_gcd_cases p a hp with
  | inl h1 =>
    right
    rcases hefez_bezout_identity p a with ⟨x, y, hbez⟩
    have hbez1 : (p : Int) * x + (a : Int) * y = 1 := by rw [hbez, h1]; rfl
    have hdvd_int : (p : Int) ∣ (a : Int) * (b : Int) := by
      have hcast : ((p : Int) ∣ ((a * b : Nat) : Int)) := Int.ofNat_dvd.2 hdvd
      exact hcast
    have hdiv_b : (p : Int) ∣ (b : Int) :=
      hefez_coprime_dvd_mul_int (p : Int) (a : Int) (b : Int) x y hbez1 hdvd_int
    exact Int.ofNat_dvd.1 hdiv_b
  | inr hp_eq =>
    left
    have hdvd_a : Nat.gcd p a ∣ a := Nat.gcd_dvd_right p a
    rw [hp_eq] at hdvd_a
    exact hdvd_a

/-!
### 3. Coeficientes Binomiais e Teorema de Stifel
-/
def binom : Nat → Nat → Nat
  | 0, 0 => 1
  | 0, _ + 1 => 0
  | _ + 1, 0 => 1
  | n + 1, k + 1 => binom n k + binom n (k + 1)

theorem binom_zero (n : Nat) : binom n 0 = 1 := by
  cases n <;> rfl

theorem binom_eq_zero_of_lt : ∀ (n k : Nat), n < k → binom n k = 0 := by
  intro n
  induction n with
  | zero =>
    intro k hk
    cases k with
    | zero => contradiction
    | succ k => rfl
  | succ n ih =>
    intro k hk
    cases k with
    | zero => contradiction
    | succ k =>
      dsimp [binom]
      have h1 : n < k := by omega
      have h2 : n < k + 1 := by omega
      rw [ih k h1, ih (k + 1) h2]

theorem binom_self (n : Nat) : binom n n = 1 := by
  induction n with
  | zero => rfl
  | succ n ih =>
    show binom n n + binom n (n + 1) = 1
    have hz : binom n (n + 1) = 0 := binom_eq_zero_of_lt n (n + 1) (by omega)
    rw [ih, hz]

theorem binom_one (n : Nat) : binom n 1 = n := by
  induction n with
  | zero => rfl
  | succ n ih =>
    show binom n 0 + binom n 1 = n + 1
    rw [binom_zero, ih, Nat.add_comm]

theorem succ_mul_plus (n X : Nat) : (n + 1) * X + X = (n + 2) * X := by
  calc
    (n + 1) * X + X = (n + 1) * X + 1 * X := by rw [Nat.one_mul]
    _ = ((n + 1) + 1) * X := (Nat.add_mul (n + 1) 1 X).symm
    _ = (n + 2) * X := rfl

theorem succ_mul_binom_succ (n k : Nat) :
    (k + 1) * binom (n + 1) (k + 1) = (n + 1) * binom n k := by
  induction n generalizing k with
  | zero =>
    cases k with
    | zero => rfl
    | succ k => rfl
  | succ n ih =>
    cases k with
    | zero =>
      show 1 * binom (n + 2) 1 = (n + 2) * binom (n + 1) 0
      rw [Nat.one_mul, binom_one, binom_zero, Nat.mul_one]
    | succ k =>
      show (k + 2) * (binom (n + 1) (k + 1) + binom (n + 1) (k + 2)) = (n + 2) * binom (n + 1) (k + 1)
      have hdistrib : (k + 2) * (binom (n + 1) (k + 1) + binom (n + 1) (k + 2)) =
                      (k + 2) * binom (n + 1) (k + 1) + (k + 2) * binom (n + 1) (k + 2) := Nat.mul_add _ _ _
      rw [hdistrib]
      rw [ih (k + 1)]
      have hsplit : (k + 2) * binom (n + 1) (k + 1) = (k + 1) * binom (n + 1) (k + 1) + binom (n + 1) (k + 1) :=
        (succ_mul_plus k (binom (n + 1) (k + 1))).symm
      rw [hsplit, ih k]
      have hdef : binom (n + 1) (k + 1) = binom n k + binom n (k + 1) := rfl
      rw [hdef]
      calc
        (n + 1) * binom n k + (binom n k + binom n (k + 1)) + (n + 1) * binom n (k + 1)
          = ((n + 1) * binom n k + binom n k) + ((n + 1) * binom n (k + 1) + binom n (k + 1)) := by omega
        _ = (n + 2) * binom n k + (n + 2) * binom n (k + 1) := by
          rw [succ_mul_plus n (binom n k), succ_mul_plus n (binom n (k + 1))]
        _ = (n + 2) * (binom n k + binom n (k + 1)) := (Nat.mul_add (n + 2) _ _).symm

theorem prime_dvd_binom (p : Nat) (hp : IsPrime p)
    (k : Nat) (hk1 : 1 ≤ k) (hk2 : k < p) :
    p ∣ binom p k := by
  obtain ⟨m, rfl⟩ : ∃ m, k = m + 1 := ⟨k - 1, by omega⟩
  have hp2 : p ≥ 2 := hp.1
  obtain ⟨p_pred, rfl⟩ : ∃ pred, p = pred + 1 := ⟨p - 1, by omega⟩
  have hid := succ_mul_binom_succ p_pred m
  have hdvd : (p_pred + 1) ∣ (m + 1) * binom (p_pred + 1) (m + 1) := by
    rw [hid]
    exact Nat.dvd_mul_right (p_pred + 1) (binom p_pred m)
  cases hefez_euclid_lemma (p_pred + 1) (m + 1) (binom (p_pred + 1) (m + 1)) hp hdvd with
  | inl h1 =>
    have hle : p_pred + 1 ≤ m + 1 := Nat.le_of_dvd (by omega) h1
    omega
  | inr h2 =>
    exact h2

/-!
### 4. Expansão Polinomial e Teorema Binomial de Newton
-/
def bsum (n a : Nat) : Nat → Nat
  | 0 => 1
  | k + 1 => bsum n a k + binom n (k + 1) * a ^ (k + 1)

theorem mul_pow_shift (B a k : Nat) : a * (B * a ^ (k + 1)) = B * a ^ (k + 1 + 1) := by
  calc
    a * (B * a ^ (k + 1)) = B * (a * a ^ (k + 1)) := by rw [Nat.mul_left_comm]
    _ = B * (a ^ (k + 1) * a) := by rw [Nat.mul_comm a (a ^ (k + 1))]
    _ = B * a ^ (k + 1 + 1) := by rw [← Nat.pow_succ]

theorem bsum_mul_add (n a : Nat) :
    ∀ k, bsum n a k + a * bsum n a k = bsum (n + 1) a k + binom n k * a ^ (k + 1) := by
  intro k
  induction k with
  | zero =>
    dsimp [bsum]
    rw [Nat.mul_one, Nat.pow_one, binom_zero n, Nat.one_mul]
  | succ k ih =>
    dsimp [bsum]
    rw [Nat.mul_add a (bsum n a k) (binom n (k + 1) * a ^ (k + 1))]
    have h1 : bsum n a k + binom n (k + 1) * a ^ (k + 1) + (a * bsum n a k + a * (binom n (k + 1) * a ^ (k + 1))) =
              (bsum n a k + a * bsum n a k) + binom n (k + 1) * a ^ (k + 1) + a * (binom n (k + 1) * a ^ (k + 1)) := by omega
    rw [h1, ih]
    have hpow := mul_pow_shift (binom n (k + 1)) a k
    rw [hpow]
    have hsum : bsum (n + 1) a k + binom n k * a ^ (k + 1) + binom n (k + 1) * a ^ (k + 1) =
                bsum (n + 1) a (k + 1) := by
      have hdistrib : binom n k * a ^ (k + 1) + binom n (k + 1) * a ^ (k + 1) =
                      (binom n k + binom n (k + 1)) * a ^ (k + 1) := by rw [Nat.add_mul]
      have hdef : binom n k + binom n (k + 1) = binom (n + 1) (k + 1) := rfl
      calc
        bsum (n + 1) a k + binom n k * a ^ (k + 1) + binom n (k + 1) * a ^ (k + 1)
          = bsum (n + 1) a k + (binom n k * a ^ (k + 1) + binom n (k + 1) * a ^ (k + 1)) := by omega
        _ = bsum (n + 1) a k + (binom n k + binom n (k + 1)) * a ^ (k + 1) := by rw [hdistrib]
        _ = bsum (n + 1) a k + binom (n + 1) (k + 1) * a ^ (k + 1) := by rw [hdef]
        _ = bsum (n + 1) a (k + 1) := rfl
    calc
      bsum (n + 1) a k + binom n k * a ^ (k + 1) + binom n (k + 1) * a ^ (k + 1) + binom n (k + 1) * a ^ (k + 1 + 1)
        = (bsum (n + 1) a k + binom n k * a ^ (k + 1) + binom n (k + 1) * a ^ (k + 1)) + binom n (k + 1) * a ^ (k + 1 + 1) := by omega
      _ = bsum (n + 1) a (k + 1) + binom n (k + 1) * a ^ (k + 1 + 1) := by rw [hsum]

theorem bsum_succ_self (n a : Nat) :
    (a + 1) * bsum n a n = bsum (n + 1) a (n + 1) := by
  have hid := bsum_mul_add n a n
  have h1 : bsum n a n + a * bsum n a n = (a + 1) * bsum n a n := by
    calc
      bsum n a n + a * bsum n a n = 1 * bsum n a n + a * bsum n a n := by rw [Nat.one_mul]
      _ = (1 + a) * bsum n a n := (Nat.add_mul 1 a (bsum n a n)).symm
      _ = (a + 1) * bsum n a n := by rw [Nat.add_comm 1 a]
  have h2 : bsum (n + 1) a n + binom n n * a ^ (n + 1) = bsum (n + 1) a (n + 1) := by
    rw [binom_self n]
    show bsum (n + 1) a n + 1 * a ^ (n + 1) = bsum (n + 1) a n + binom (n + 1) (n + 1) * a ^ (n + 1)
    rw [binom_self (n + 1)]
  rw [← h1, ← h2, hid]

theorem bsum_eq_pow (n a : Nat) : bsum n a n = (a + 1) ^ n := by
  induction n with
  | zero => rfl
  | succ n ih =>
    calc
      bsum (n + 1) a (n + 1) = (a + 1) * bsum n a n := (bsum_succ_self n a).symm
      _ = (a + 1) * (a + 1) ^ n := by rw [ih]
      _ = (a + 1) ^ n * (a + 1) := by rw [Nat.mul_comm]
      _ = (a + 1) ^ (n + 1) := by rw [← Nat.pow_succ]

theorem one_le_bsum (n a : Nat) : ∀ k, 1 ≤ bsum n a k := by
  intro k
  induction k with
  | zero =>
    dsimp [bsum]
    omega
  | succ k ih =>
    dsimp [bsum]
    omega

theorem dvd_bsum_sub_one (p a : Nat) (hp : IsPrime p) :
    ∀ k, k < p → p ∣ (bsum p a k - 1) := by
  intro k
  induction k with
  | zero =>
    intro _
    dsimp [bsum]
    exact Nat.dvd_zero p
  | succ k ih =>
    intro hlt
    dsimp [bsum]
    have hlt_k : k < p := by omega
    have ih_k := ih hlt_k
    have hdvd_binom : p ∣ binom p (k + 1) := prime_dvd_binom p hp (k + 1) (by omega) hlt
    have hdvd_binom_term : p ∣ binom p (k + 1) * a ^ (k + 1) :=
      Nat.dvd_trans hdvd_binom (Nat.dvd_mul_right (binom p (k + 1)) (a ^ (k + 1)))
    have hrew : bsum p a k + binom p (k + 1) * a ^ (k + 1) - 1 =
                (bsum p a k - 1) + binom p (k + 1) * a ^ (k + 1) := by
      have : 1 ≤ bsum p a k := one_le_bsum p a k
      omega
    rw [hrew]
    exact Nat.dvd_add ih_k hdvd_binom_term

theorem ofNat_sub_of_add_mul (X Y P Q : Nat) (h : X = Y + P * Q) :
    (X : Int) - (Y : Int) = (P : Int) * (Q : Int) := by
  have hc : (X : Int) = (Y : Int) + (P : Int) * (Q : Int) := by
    calc
      (X : Int) = ((Y + P * Q : Nat) : Int) := congrArg Int.ofNat h
      _ = (Y : Int) + ((P * Q : Nat) : Int) := rfl
      _ = (Y : Int) + (P : Int) * (Q : Int) := rfl
  omega

theorem cong_succ_pow (p a : Nat) (hp : IsPrime p) :
    Congruent (((a + 1) ^ p : Nat) : Int) (((a ^ p + 1 : Nat) : Int)) (p : Int) := by
  dsimp [Congruent]
  have hp2 : p ≥ 2 := hp.1
  obtain ⟨p_pred, rfl⟩ : ∃ pred, p = pred + 1 := ⟨p - 1, by omega⟩
  have hdvd_mid := dvd_bsum_sub_one (p_pred + 1) a hp p_pred (by omega)
  obtain ⟨q, hq⟩ := hdvd_mid
  have hpow := (bsum_eq_pow (p_pred + 1) a).symm
  have hsplit : bsum (p_pred + 1) a (p_pred + 1) =
                bsum (p_pred + 1) a p_pred + a ^ (p_pred + 1) := by
    show bsum (p_pred + 1) a p_pred + binom (p_pred + 1) (p_pred + 1) * a ^ (p_pred + 1) =
         bsum (p_pred + 1) a p_pred + a ^ (p_pred + 1)
    rw [binom_self (p_pred + 1), Nat.one_mul]
  have hmid_eq : bsum (p_pred + 1) a p_pred = (p_pred + 1) * q + 1 := by
    have : 1 ≤ bsum (p_pred + 1) a p_pred := one_le_bsum (p_pred + 1) a p_pred
    omega
  have hid_nat : (a + 1) ^ (p_pred + 1) = (a ^ (p_pred + 1) + 1) + (p_pred + 1) * q := by
    calc
      (a + 1) ^ (p_pred + 1) = bsum (p_pred + 1) a (p_pred + 1) := hpow
      _ = bsum (p_pred + 1) a p_pred + a ^ (p_pred + 1) := hsplit
      _ = (p_pred + 1) * q + 1 + a ^ (p_pred + 1) := by rw [hmid_eq]
      _ = (a ^ (p_pred + 1) + 1) + (p_pred + 1) * q := by omega
  refine ⟨(q : Int), ?_⟩
  exact ofNat_sub_of_add_mul ((a + 1) ^ (p_pred + 1)) (a ^ (p_pred + 1) + 1) (p_pred + 1) q hid_nat

theorem ofNat_zero_pow (p : Nat) (hp : p ≥ 1) : (((0 : Nat) ^ p : Nat) : Int) = 0 := by
  cases p with
  | zero => contradiction
  | succ p => rfl

theorem ofNat_pow (a k : Nat) : ((a ^ k : Nat) : Int) = (a : Int) ^ k := by
  induction k with
  | zero => rfl
  | succ k ih =>
    change ((a ^ k * a : Nat) : Int) = (a : Int) ^ k * (a : Int)
    have : ((a ^ k * a : Nat) : Int) = ((a ^ k : Nat) : Int) * (a : Int) := rfl
    rw [this, ih]

/-!
### 5. Pequeno Teorema de Fermat: Forma Aditiva Canônica (a^p ≡ a mod p)
-/
theorem fermat_little_congruence (p : Nat) (hp : IsPrime p) :
    ∀ a : Nat, Congruent (((a ^ p : Nat) : Int)) (a : Int) (p : Int) := by
  intro a
  induction a with
  | zero =>
    have hp2 : p ≥ 2 := hp.1
    rw [ofNat_zero_pow p (by omega)]
    exact cong_refl 0 (p : Int)
  | succ a ih =>
    have hstep := cong_succ_pow p a hp
    have hone : Congruent (1 : Int) (1 : Int) (p : Int) := cong_refl 1 (p : Int)
    have hih_add : Congruent (((a ^ p : Nat) : Int) + 1) ((a : Int) + 1) (p : Int) :=
      cong_add (((a ^ p : Nat) : Int)) (a : Int) 1 1 (p : Int) ih hone
    have h_trans : Congruent (((a + 1) ^ p : Nat) : Int) ((a : Int) + 1) (p : Int) :=
      cong_trans (((a + 1) ^ p : Nat) : Int) (((a ^ p + 1 : Nat) : Int)) ((a : Int) + 1) (p : Int) hstep hih_add
    exact h_trans

/-!
### 6. Pequeno Teorema de Fermat: Forma Multiplicativa Clássica (a^(p-1) ≡ 1 mod p)
Para qualquer natural a coprimo com p, a^(p-1) deixa resto 1 na divisão por p.
-/
theorem int_mul_sub_one (a X : Int) : a * X - a = a * (X - 1) := by
  calc
    a * X - a = a * X - a * 1 := by rw [Int.mul_one]
    _ = a * (X - 1) := (Int.mul_sub a X 1).symm

theorem int_pow_succ_eq (a : Int) (pred : Nat) :
    a ^ (pred + 1) = a * a ^ pred := by
  rw [Int.pow_succ, Int.mul_comm]

theorem int_pow_succ_sub (a : Int) (pred : Nat) :
    a ^ (pred + 1) - a = a * (a ^ pred - 1) := by
  rw [int_pow_succ_eq a pred]
  exact int_mul_sub_one a (a ^ pred)

theorem fermat_little_coprime (p a : Nat) (hp : IsPrime p) (hcoprime : Nat.gcd a p = 1) :
    Congruent (((a ^ (p - 1) : Nat) : Int)) 1 (p : Int) := by
  have hp2 : p ≥ 2 := hp.1
  obtain ⟨p_pred, rfl⟩ : ∃ pred, p = pred + 1 := ⟨p - 1, by omega⟩
  have hcong := fermat_little_congruence (p_pred + 1) hp a
  rw [ofNat_pow a (p_pred + 1)] at hcong
  dsimp [Congruent] at hcong
  have hid := int_pow_succ_sub (a : Int) p_pred
  rw [hid] at hcong
  have hgcd_pa : Nat.gcd (p_pred + 1) a = 1 := by
    rw [Nat.gcd_comm]
    exact hcoprime
  rcases hefez_bezout_identity (p_pred + 1) a with ⟨x, y, hbez⟩
  have hbez1 : ((p_pred + 1 : Nat) : Int) * x + (a : Int) * y = 1 := by
    rw [hbez, hgcd_pa]
    rfl
  have hdvd : ((p_pred + 1 : Nat) : Int) ∣ ((a : Int) ^ p_pred - 1) :=
    hefez_coprime_dvd_mul_int ((p_pred + 1 : Nat) : Int) (a : Int) ((a : Int) ^ p_pred - 1) x y hbez1 hcong
  dsimp [Congruent]
  have : p_pred + 1 - 1 = p_pred := rfl
  change ((p_pred + 1 : Nat) : Int) ∣ (((a ^ p_pred : Nat) : Int)) - 1
  rw [ofNat_pow a p_pred]
  exact hdvd

/-!
### 7. Exemplos Numéricos Históricos e Verificação Algébrica (#eval)
Exemplo 1: a = 2, p = 5 ⟹ 2^4 = 16 ≡ 1 mod 5
Exemplo 2: a = 3, p = 7 ⟹ 3^6 = 729 ≡ 1 mod 7
Exemplo 3: a = 2, p = 11 ⟹ 2^10 = 1024 ≡ 1 mod 11
Exemplo 4: a = 2, p = 5 ⟹ 2^5 = 32 ≡ 2 mod 5
-/
example : Congruent (((2 ^ 4 : Nat) : Int)) 1 5 := by
  dsimp [Congruent]
  refine ⟨3, by decide⟩

example : Congruent (((3 ^ 6 : Nat) : Int)) 1 7 := by
  dsimp [Congruent]
  refine ⟨104, by decide⟩

example : Congruent (((2 ^ 10 : Nat) : Int)) 1 11 := by
  dsimp [Congruent]
  refine ⟨93, by decide⟩

example : Congruent (((2 ^ 5 : Nat) : Int)) 2 5 := by
  dsimp [Congruent]
  refine ⟨6, by decide⟩

#eval (2 ^ 4 - 1) % 5 == 0
#eval (3 ^ 6 - 1) % 7 == 0
#eval (2 ^ 10 - 1) % 11 == 0
#eval (2 ^ 5 - 2) % 5 == 0

end Dia11Fermat
