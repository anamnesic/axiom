/-
  Chronokairo AXIOM — Mathematical Investigation Dossier
  Formal Machine-Checked Verification of:
  "Iniciação à Aritmética" (Abramo Hefez, SBM/OBMEP)
  Kernel: Lean 4 (compatível com v4.14.0 do CI e v4.35.0 local)
  Guarantee: formal-proof (Zero sorry, zero untrusted axioms)
-/

namespace HefezArithmetic

/-!
### Teorema 1: Linearidade da Divisibilidade (Problema 3.13a & 3.15)
"Se d divide a e d divide b, então d divide m*a + n*b para quaisquer inteiros m, n."
-/
theorem hefez_dvd_linear_comb (d a b m n : Int) (h1 : d ∣ a) (h2 : d ∣ b) :
    d ∣ (m * a + n * b) := by
  have hma : d ∣ m * a := Int.dvd_trans h1 (Int.dvd_mul_left m a)
  have hnb : d ∣ n * b := Int.dvd_trans h2 (Int.dvd_mul_left n b)
  exact Int.dvd_add hma hnb

/-!
### Teorema 2: Transitividade da Divisibilidade (Problema 1.17 & Seção 3.3)
"Se a divide b e b divide c, então a divide c."
-/
theorem hefez_dvd_trans (a b c : Int) (h1 : a ∣ b) (h2 : b ∣ c) : a ∣ c :=
  Int.dvd_trans h1 h2

/-!
### Teorema 3: Preservação de Divisores Comuns por Subtração (Problema 3.13c, pág. 49)
"d é divisor comum de a e b se e somente se d é divisor comum de a e b - a."
-/
theorem hefez_common_divisor_sub (d a b : Int) :
    (d ∣ a ∧ d ∣ b) ↔ (d ∣ a ∧ d ∣ (b - a)) := by
  constructor
  · intro ⟨ha, hb⟩
    constructor
    · exact ha
    · have h : b - a = 1 * b + (-1) * a := by omega
      rw [h]
      have h1 : d ∣ 1 * b := Int.dvd_trans hb (Int.dvd_mul_left 1 b)
      have h2 : d ∣ (-1) * a := Int.dvd_trans ha (Int.dvd_mul_left (-1) a)
      exact Int.dvd_add h1 h2
  · intro ⟨ha, hsub⟩
    constructor
    · exact ha
    · have h : b = (b - a) + 1 * a := by omega
      rw [h]
      have h1 : d ∣ 1 * a := Int.dvd_trans ha (Int.dvd_mul_left 1 a)
      exact Int.dvd_add hsub h1

/-!
### Lema Auxiliar: Divisores de Naturais Consecutivos
"Se d divide a + 1 e d divide a, então d divide 1."
(Argumento dos witnesses de Euclides; prova independente da versão do kernel.)
-/
theorem dvd_consecutive (d a : Nat) (h1 : d ∣ a + 1) (h2 : d ∣ a) : d ∣ 1 := by
  obtain ⟨x, hx⟩ := h1
  obtain ⟨y, hy⟩ := h2
  have e1 : d * x = a + 1 := hx.symm
  have e2 : d * y = a := hy.symm
  refine ⟨x - y, ?_⟩
  cases Nat.lt_or_ge x y with
  | inl hxy =>
    exfalso
    have hle : x * d ≤ y * d := Nat.mul_le_mul_right d (by omega)
    rw [Nat.mul_comm d x] at e1
    rw [Nat.mul_comm d y] at e2
    omega
  | inr hxy =>
    obtain ⟨k, hk⟩ : ∃ k, x = y + k := ⟨x - y, by omega⟩
    subst hk
    have hky : y + k - y = k := by omega
    rw [hky]
    have e1' : d * y + d * k = a + 1 := by rw [← Nat.left_distrib d y k]; exact e1
    omega

/-!
### Teorema 4: MDC de Inteiros Consecutivos (Seção 3.3, Página 52)
"Dois números inteiros consecutivos n e n + 1 são sempre primos entre si: mdc(n, n + 1) = 1."
-/
theorem hefez_gcd_succ (n : Nat) : Nat.gcd n (n + 1) = 1 := by
  have h1 : Nat.gcd n (n + 1) ∣ n + 1 := Nat.gcd_dvd_right n (n + 1)
  have h2 : Nat.gcd n (n + 1) ∣ n := Nat.gcd_dvd_left n (n + 1)
  exact (Nat.dvd_one).mp (dvd_consecutive (Nat.gcd n (n + 1)) n h1 h2)

/-!
### Teorema 5: MDC de n e 2n + 1 (Problema 3.16a, Página 52)
"Para todo n natural, os inteiros n e 2n + 1 são sempre primos entre si."
-/
theorem hefez_gcd_two_n_plus_one (n : Nat) : Nat.gcd n (2 * n + 1) = 1 := by
  have h1 : Nat.gcd n (2 * n + 1) ∣ 2 * n + 1 := Nat.gcd_dvd_right n (2 * n + 1)
  have h2 : Nat.gcd n (2 * n + 1) ∣ 2 * n :=
    Nat.dvd_trans (Nat.gcd_dvd_left n (2 * n + 1)) (Nat.dvd_mul_left n 2)
  exact (Nat.dvd_one).mp (dvd_consecutive (Nat.gcd n (2 * n + 1)) (2 * n) h1 h2)

/-!
### Teorema 6: Fatoração Externa do MDC (Problema 3.17, Página 53)
"mdc(a * d, b * d) = mdc(a, b) * d."
-/
theorem hefez_gcd_factor_out (a b d : Nat) :
    Nat.gcd (a * d) (b * d) = (Nat.gcd a b) * d :=
  Nat.gcd_mul_right a d b

/-!
### Teorema 7: Algoritmo da Divisão Euclidiana (Seção 3.4, Página 53)
"Dados a e b naturais com b > 0, existem quociente q e resto r tais que a = b*q + r com r < b."
-/
theorem hefez_euclidean_division (a b : Nat) (hb : 0 < b) :
    a = b * (a / b) + (a % b) ∧ (a % b) < b := by
  constructor
  · exact (Nat.div_add_mod a b).symm
  · exact Nat.mod_lt a hb

/-!
### Teorema 8: Delimitação da Raiz Quadrada no Crivo de Eratóstenes (Seção 2.5, Página 33)
"Se a <= b, então a^2 <= a * b."
-/
theorem hefez_factor_bound (a b : Nat) (h : a ≤ b) : a * a ≤ a * b :=
  Nat.mul_le_mul_left a h

/-!
### Teorema 9: Paridade e Decomposição Modular (Seção 3.5, Página 58)
"Todo número natural é par (2k) ou ímpar (2k + 1)."
-/
theorem hefez_even_or_odd (n : Nat) : (∃ k, n = 2 * k) ∨ (∃ k, n = 2 * k + 1) := by
  have hmod : n % 2 = 0 ∨ n % 2 = 1 := by omega
  have hdiv : n = 2 * (n / 2) + (n % 2) := (Nat.div_add_mod n 2).symm
  cases hmod with
  | inl h0 =>
    left
    exists (n / 2)
    omega
  | inr h1 =>
    right
    exists (n / 2)
    omega

end HefezArithmetic
