/-
  Chronokairo AXIOM — Mathematical Investigation Dossier
  Dia 07: Teorema Fundamental da Aritmética — Unicidade da Decomposição em Primos
  Referência: "Iniciação à Aritmética" (Abramo Hefez, SBM/OBMEP), Cap. 2.1, 2.2 e 2.3, pág. 34-36.
  Kernel: Lean 4 (compatível com v4.14.0 do CI e v4.35.0 local)
  Garantia Epistêmica: formal-proof (Machine-checked, zero sorry, zero untrusted axioms)
-/

namespace Dia07TFAUniqueness

/-!
### 1. Definição Epistêmica de Número Primo (Abramo Hefez, Cap. 2)
"Um número natural p ≥ 2 diz-se um número primo se os seus únicos divisores
positivos forem 1 e p."
-/
def IsPrime (p : Nat) : Prop :=
  p ≥ 2 ∧ ∀ d : Nat, d ∣ p → d = 1 ∨ d = p

theorem prime_ge_two (p : Nat) (hp : IsPrime p) : p ≥ 2 := hp.1

theorem prime_dvd_prime (p q : Nat) (hp : IsPrime p) (hq : IsPrime q) (hdvd : p ∣ q) : p = q := by
  have := hq.2 p hdvd
  cases this with
  | inl h1 =>
    have : p ≥ 2 := hp.1
    omega
  | inr h2 => exact h2

theorem not_dvd_one_of_ge_two (p : Nat) (hp : p ≥ 2) : ¬ (p ∣ 1) := by
  intro h
  have : p ≤ 1 := Nat.le_of_dvd (by decide) h
  omega

/-!
### 2. Fundações Algébricas da Coprimaridade e Lema de Euclides (Hefez, Cap. 2.6 & 3.9)
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
    exact hefez_coprime_dvd_mul p a b h1 hdvd
  | inr hp_eq =>
    left
    have hdvd_a : Nat.gcd p a ∣ a := Nat.gcd_dvd_right p a
    rw [hp_eq] at hdvd_a
    exact hdvd_a

/-!
### 3. Lemas Aritméticos de Listas de Fatores e Produtos

`List.prod` entrou no core do Lean 4 após a v4.14.0 usada pelo CI; para
independência de versão do kernel, definimos localmente o produto de uma
lista com as propriedades algébricas necessárias à decomposição em primos.
-/
def listProd : List Nat → Nat
  | [] => 1
  | a :: t => a * listProd t

theorem listProd_nil : listProd [] = 1 := rfl

theorem listProd_cons (a : Nat) (t : List Nat) : listProd (a :: t) = a * listProd t := rfl

theorem listProd_append (s t : List Nat) : listProd (s ++ t) = listProd s * listProd t := by
  induction s with
  | nil => rw [List.nil_append, listProd_nil, Nat.one_mul]
  | cons a s ih =>
    rw [List.cons_append, listProd_cons, listProd_cons, ih,
      Nat.mul_assoc a (listProd s) (listProd t)]

theorem prod_split (a : Nat) (s t : List Nat) :
    listProd (s ++ a :: t) = a * listProd (s ++ t) := by
  rw [listProd_append, listProd_cons, listProd_append]
  rw [← Nat.mul_assoc, Nat.mul_comm (listProd s) a, Nat.mul_assoc]

theorem empty_of_prod_one (L : List Nat) (hprimes : ∀ q ∈ L, IsPrime q) (hprod : listProd L = 1) :
    L = [] := by
  cases L with
  | nil => rfl
  | cons x xs =>
    rw [listProd_cons] at hprod
    have hx_prime : IsPrime x := hprimes x (List.Mem.head xs)
    have hx_ge : x ≥ 2 := hx_prime.1
    have hx_dvd : x ∣ 1 := ⟨listProd xs, hprod.symm⟩
    have hx_le : x ≤ 1 := Nat.le_of_dvd (by decide) hx_dvd
    omega

theorem prime_dvd_prod (p : Nat) (L : List Nat) (hp : IsPrime p) (hdvd : p ∣ listProd L) :
    ∃ q ∈ L, p ∣ q := by
  induction L with
  | nil =>
    rw [listProd_nil] at hdvd
    exfalso
    exact not_dvd_one_of_ge_two p hp.1 hdvd
  | cons x xs ih =>
    rw [listProd_cons] at hdvd
    cases hefez_euclid_lemma p x (listProd xs) hp hdvd with
    | inl hx => exact ⟨x, List.Mem.head xs, hx⟩
    | inr hxs =>
      rcases ih hxs with ⟨q, hq_mem, hq_dvd⟩
      exact ⟨q, List.Mem.tail x hq_mem, hq_dvd⟩

theorem prime_mem_of_dvd_prod (p : Nat) (L : List Nat) (hp : IsPrime p)
    (hprimes : ∀ q ∈ L, IsPrime q) (hdvd : p ∣ listProd L) : p ∈ L := by
  rcases prime_dvd_prod p L hp hdvd with ⟨q, hq_mem, hq_dvd⟩
  have hq_prime := hprimes q hq_mem
  have heq := prime_dvd_prime p q hp hq_prime hq_dvd
  subst heq
  exact hq_mem

/-!
### 4. Teorema Fundamental da Aritmética — Unicidade (Abramo Hefez, Teorema 2.2)
"A decomposição de qualquer número natural n ≥ 2 em fatores primos é única,
a menos da ordem dos fatores."

Demonstração (Hefez):
Se L1 e L2 são listas de números primos tais que prod L1 = prod L2:
- Caso base (L1 = []): prod L1 = 1, o que implica que L2 só pode ser vazia (pois qualquer
  elemento primo seria ≥ 2, tornando prod L2 ≥ 2 > 1).
- Passo indutivo (L1 = p :: xs): Como p divide prod L1, p divide prod L2.
  Pelo Lema de Euclides iterado, p deve dividir algum elemento q de L2.
  Como q é primo, p = q, logo p ∈ L2.
  Podemos então decompor L2 = s ++ p :: t, que é uma permutação de p :: (s ++ t).
  Cancelando o fator p > 0 em ambos os lados, obtemos prod xs = prod (s ++ t).
  Por hipótese de indução sobre xs, xs é uma permutação de s ++ t.
  Portanto, p :: xs é uma permutação de s ++ p :: t = L2.
-/
theorem hefez_fundamental_theorem_uniqueness (L1 L2 : List Nat)
    (h1 : ∀ p ∈ L1, IsPrime p)
    (h2 : ∀ q ∈ L2, IsPrime q)
    (hprod : listProd L1 = listProd L2) :
    L1.Perm L2 := by
  induction L1 generalizing L2 with
  | nil =>
    rw [listProd_nil] at hprod
    have hL2_nil := empty_of_prod_one L2 h2 hprod.symm
    subst hL2_nil
    exact List.Perm.nil
  | cons p xs ih =>
    have hp : IsPrime p := h1 p (List.Mem.head xs)
    have hxs : ∀ q ∈ xs, IsPrime q := fun q hq => h1 q (List.Mem.tail p hq)
    have hp_dvd_L1 : p ∣ listProd (p :: xs) := by
      rw [listProd_cons]
      exact Nat.dvd_mul_right p (listProd xs)
    have hp_dvd_L2 : p ∣ listProd L2 := by
      rw [← hprod]
      exact hp_dvd_L1
    have hp_in_L2 : p ∈ L2 := prime_mem_of_dvd_prod p L2 hp h2 hp_dvd_L2
    obtain ⟨s, t, rfl⟩ := List.mem_iff_append.1 hp_in_L2
    have hperm_L2 : (p :: (s ++ t)).Perm (s ++ p :: t) := List.perm_middle.symm
    have h_primes_st : ∀ q ∈ s ++ t, IsPrime q := by
      intro q hq
      cases List.mem_append.1 hq with
      | inl hs =>
        apply h2
        rw [List.mem_append]
        exact Or.inl hs
      | inr ht =>
        apply h2
        rw [List.mem_append]
        right
        exact List.Mem.tail p ht
    have hprod_st : listProd xs = listProd (s ++ t) := by
      rw [listProd_cons] at hprod
      rw [prod_split p s t] at hprod
      have hp_pos : p > 0 := by
        have := hp.1
        omega
      exact Nat.eq_of_mul_eq_mul_left hp_pos hprod
    have ih_perm := ih (s ++ t) hxs h_primes_st hprod_st
    have hcons_perm : (p :: xs).Perm (p :: (s ++ t)) := List.Perm.cons p ih_perm
    exact List.Perm.trans hcons_perm hperm_L2

-- Exemplo computacional canônico de Abramo Hefez (pág. 34-35)
def L_canonical : List Nat := [2, 2, 2, 3, 3, 5]
def L_permuted : List Nat := [3, 2, 5, 2, 3, 2]

#eval listProd L_canonical == 360 && listProd L_permuted == 360

end Dia07TFAUniqueness
