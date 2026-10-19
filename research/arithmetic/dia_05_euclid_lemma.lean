/-
  Chronokairo AXIOM — Mathematical Investigation Dossier
  Dia 05: Lema de Euclides para Números Primos
  Referência: "Iniciação à Aritmética" (Abramo Hefez, SBM/OBMEP), Cap. 2.6, pág. 37-40; Seção 3.9, pág. 70-71.
  Kernel: Lean 4 (version 4.35.0)
  Garantia Epistêmica: formal-proof (Machine-checked, zero sorry, zero untrusted axioms)
-/

namespace Dia05EuclidLemma

/-!
### 1. Definição Epistêmica de Número Primo (Abramo Hefez, Cap. 2)
"Um número natural p ≥ 2 diz-se um número primo se os seus únicos divisores
positivos forem 1 e p."
-/
def IsPrime (p : Nat) : Prop :=
  p ≥ 2 ∧ ∀ d : Nat, d ∣ p → d = 1 ∨ d = p

/-!
### 2. Lema Auxiliar de Retrosubstituição Euclidiana
Base linear para a identidade de Bézout comprovada no Dia 04.
-/
theorem hefez_bezout_algebra (m t s q r : Int) :
    m * (t - s * q) + (m * q + r) * s = r * s + m * t := by
  have h1 : m * (t - s * q) = m * t - m * (s * q) := Int.mul_sub m t (s * q)
  have h2 : (m * q + r) * s = (m * q) * s + r * s := Int.add_mul (m * q) r s
  have h3 : m * (s * q) = (m * q) * s := by
    rw [Int.mul_assoc, Int.mul_comm s q, ← Int.mul_assoc]
  rw [h1, h2, h3]
  omega

/-!
### 3. Identidade de Bézout em ℤ (Hefez, Teorema 3.3)
Garante a existência dos coeficientes inteiros de combinação linear para o MDC.
-/
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

/-!
### 4. Lema de Coprimaridade Linear em ℤ (Hefez, Corolário 3.4)
"Se a*x + b*y = 1 e a divide b*c, então a divide c."
Demonstração: c = 1*c = (ax + by)*c = a*(xc) + (bc)*y. Como a divide ambos os termos,
a divide sua soma c.
-/
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

/-!
### 5. Lema de Divisibilidade para Números Coprimos em ℕ (Hefez, pág. 71)
"Se mdc(a, b) = 1 e a divide b*c, então a divide c."
-/
theorem hefez_coprime_dvd_mul (a b c : Nat)
    (hcoprime : Nat.gcd a b = 1)
    (hdvd : a ∣ b * c) :
    a ∣ c := by
  rcases hefez_bezout_identity a b with ⟨x, y, hbez⟩
  have hbez1 : (a : Int) * x + (b : Int) * y = 1 := by
    rw [hbez]
    rw [hcoprime]
    rfl
  have hdvd_int : (a : Int) ∣ (b : Int) * (c : Int) := by
    have hcast : ((a : Int) ∣ ((b * c : Nat) : Int)) := Int.ofNat_dvd.2 hdvd
    exact hcast
  have hdiv_c : (a : Int) ∣ (c : Int) :=
    hefez_coprime_dvd_mul_int (a : Int) (b : Int) (c : Int) x y hbez1 hdvd_int
  exact Int.ofNat_dvd.1 hdiv_c

/-!
### 6. Dicotomia do MDC com um Número Primo
"Para qualquer número primo p e qualquer natural a, ou mdc(p, a) = 1 ou mdc(p, a) = p."
Decorre diretamente do fato de mdc(p, a) ser divisor de p, e p só ter 1 e p como divisores.
-/
theorem hefez_prime_gcd_cases (p a : Nat) (hp : IsPrime p) :
    Nat.gcd p a = 1 ∨ Nat.gcd p a = p := by
  have hdvd : Nat.gcd p a ∣ p := Nat.gcd_dvd_left p a
  exact hp.2 (Nat.gcd p a) hdvd

/-!
### 7. Lema Fundamental de Euclides para Números Primos (Hefez, Cap. 2.6 / Prop. 2.6)
"Se p é um número primo e p divide o produto a*b, então p divide a ou p divide b."
Demonstração (Abramo Hefez):
Pela dicotomia do MDC:
- Se mdc(p, a) = p: como mdc(p, a) divide a, segue que p divide a.
- Se mdc(p, a) = 1: como p e a são coprimos e p divide a*b, pelo Lema de Coprimaridade, p divide b.
Em qualquer caso, p ∣ a ou p ∣ b.
-/
theorem hefez_euclid_lemma (p a b : Nat)
    (hp : IsPrime p)
    (hdvd : p ∣ a * b) :
    p ∣ a ∨ p ∣ b := by
  cases hefez_prime_gcd_cases p a hp with
  | inl h1 =>
    right
    exact hefez_coprime_dvd_mul p a b h1 hdvd
  | inr hp_eq =>
    left
    have hdvd_a : Nat.gcd p a ∣ a := Nat.gcd_dvd_right p a
    rw [hp_eq] at hdvd_a
    exact hdvd_a

end Dia05EuclidLemma
