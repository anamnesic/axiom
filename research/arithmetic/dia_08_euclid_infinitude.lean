/-
  Chronokairo AXIOM — Mathematical Investigation Dossier
  Dia 08: Teorema de Euclides — Infinitude dos Números Primos
  Referência: "Iniciação à Aritmética" (Abramo Hefez, SBM/OBMEP), Cap. 2.4, pág. 40.
  Kernel: Lean 4 (compatível com v4.14.0 do CI e v4.35.0 local)
  Garantia Epistêmica: formal-proof (Machine-checked, zero sorry, zero untrusted axioms)

  Enunciado canônico (Hefez, pág. 40):
  "Suponha por absurdo que os números primos sejam em número finito e seja a o
  produto de todos eles. O número a+1 não seria primo pois ele seria maior do
  que qualquer número primo. Logo, a+1 sendo composto, ele seria múltiplo de
  algum número primo q. Mas sendo a também múltiplo de q, teríamos, pelo
  Problema 1.21, que 1 seria múltiplo do número primo q, o que é um absurdo."

  Conteúdo construtivo (meta do checklist):
  Para todo n ∈ ℕ existe um primo p > n. A testemunha construtiva é o menor
  fator primo de n! + 1: nenhum primo q ≤ n divide n! + 1, pois q ∣ n! e
  q ∣ n! + 1 implicariam q ∣ 1, absurdo para q ≥ 2.
-/

namespace Dia08EuclidInfinitude

/-!
### 1. Definição Epistêmica de Número Primo (Abramo Hefez, Cap. 2)
"Um número natural p ≥ 2 diz-se um número primo se os seus únicos divisores
positivos forem 1 e p."
-/
def IsPrime (p : Nat) : Prop :=
  p ≥ 2 ∧ ∀ d : Nat, d ∣ p → d = 1 ∨ d = p

/-!
### 2. Fatorial (autossuficiente, sem Mathlib)
-/
def fact : Nat → Nat
  | 0 => 1
  | n + 1 => (n + 1) * fact n

theorem fact_pos (n : Nat) : 1 ≤ fact n := by
  induction n with
  | zero => exact Nat.le_refl 1
  | succ n ih =>
    exact Nat.succ_le_of_lt
      (Nat.mul_pos (Nat.succ_pos n) (Nat.lt_of_lt_of_le Nat.zero_lt_one ih))

/-!
### 3. Busca Construtiva do Menor Fator ≥ 2 (Hefez, Lema 2.1)
`minFacAux fuel n k` percorre k, k+1, k+2, ... até encontrar o primeiro
divisor de n não inferior a k, retornando n quando k alcança n.
-/
def minFacAux : Nat → Nat → Nat → Nat
  | 0, n, _ => n
  | fuel + 1, n, k =>
    if n ≤ k then n
    else if n % k = 0 then k
    else minFacAux fuel n (k + 1)

def minFac (n : Nat) : Nat := minFacAux n n 2

/-!
### 4. Especificação Formal da Busca: Divisibilidade, Limite Inferior e Minimalidade
O invariante `hinv` ("nenhum fator de n é ≥ 2 e < k") garante que o resultado
é o MENOR divisor ≥ 2 de n; o combustível `n ≤ k + fuel` garante que a busca
não excede o orçamento antes de k alcança n.
-/
theorem minFacAux_spec (fuel : Nat) (n : Nat) (hn : 2 ≤ n) :
    ∀ k, 2 ≤ k → k ≤ n → n ≤ k + fuel →
      (∀ e, 2 ≤ e → e ∣ n → k ≤ e) →
      2 ≤ minFacAux fuel n k ∧ minFacAux fuel n k ∣ n ∧
        ∀ e, 2 ≤ e → e ∣ n → minFacAux fuel n k ≤ e := by
  induction fuel with
  | zero =>
    intro k hk hkn hfuel hinv
    have hdef : minFacAux 0 n k = n := rfl
    rw [hdef]
    refine ⟨hn, Nat.dvd_refl n, ?_⟩
    intro e he hdvd
    have h1 : n ≤ k := by omega
    have h2 : k ≤ e := hinv e he hdvd
    omega
  | succ fuel ih =>
    intro k hk hkn hfuel hinv
    have heq : minFacAux (fuel + 1) n k
        = if n ≤ k then n else if n % k = 0 then k else minFacAux fuel n (k + 1) := rfl
    rw [heq]
    by_cases h1 : n ≤ k
    · rw [if_pos h1]
      refine ⟨hn, Nat.dvd_refl n, ?_⟩
      intro e he hdvd
      have h2 : k ≤ e := hinv e he hdvd
      omega
    · rw [if_neg h1]
      by_cases h2 : n % k = 0
      · rw [if_pos h2]
        refine ⟨hk, Nat.dvd_of_mod_eq_zero h2, ?_⟩
        intro e he hdvd
        exact hinv e he hdvd
      · rw [if_neg h2]
        have hkn' : k + 1 ≤ n := by omega
        have hfuel' : n ≤ (k + 1) + fuel := by omega
        have hinv' : ∀ e, 2 ≤ e → e ∣ n → k + 1 ≤ e := by
          intro e he hdvd
          have hke : k ≤ e := hinv e he hdvd
          cases Nat.lt_or_ge e (k + 1) with
          | inl hlt =>
            exfalso
            have hek : e = k := by omega
            subst hek
            exact h2 (Nat.mod_eq_zero_of_dvd hdvd)
          | inr hge => exact hge
        exact ih (k + 1) (by omega) hkn' hfuel' hinv'

theorem minFac_spec (n : Nat) (hn : 2 ≤ n) :
    2 ≤ minFac n ∧ minFac n ∣ n ∧ ∀ e, 2 ≤ e → e ∣ n → minFac n ≤ e :=
  minFacAux_spec n n hn 2 (by decide) (by omega) (by omega) (fun _ he _ => he)

/-!
### 5. O Menor Fator ≥ 2 de n ≥ 2 é Primo
Se e ≥ 2 divide minFac n, então e divide n, logo a minimalidade força
minFac n ≤ e; combinada com e ∣ minFac n, resta e = minFac n.
-/
theorem minFac_prime (n : Nat) (hn : 2 ≤ n) : IsPrime (minFac n) := by
  obtain ⟨hd2, hd_dvd, hd_min⟩ := minFac_spec n hn
  refine ⟨hd2, ?_⟩
  intro e he_dvd
  cases e with
  | zero =>
    exfalso
    have h0 : minFac n = 0 := Nat.eq_zero_of_zero_dvd he_dvd
    omega
  | succ e1 =>
    cases e1 with
    | zero => left; rfl
    | succ e2 =>
      right
      have he_ge : 2 ≤ e2 + 2 := by omega
      have he_dvd_n : (e2 + 2) ∣ n := Nat.dvd_trans he_dvd hd_dvd
      have hle : minFac n ≤ e2 + 2 := hd_min (e2 + 2) he_ge he_dvd_n
      obtain ⟨j, hj⟩ := he_dvd
      cases j with
      | zero =>
        exfalso
        rw [Nat.mul_zero] at hj
        omega
      | succ j' =>
        have hge : e2 + 2 ≤ minFac n := by
          rw [hj]
          calc e2 + 2 = (e2 + 2) * 1 := (Nat.mul_one (e2 + 2)).symm
            _ ≤ (e2 + 2) * (j' + 1) := Nat.mul_le_mul_left (e2 + 2) (by omega)
        exact Nat.le_antisymm hge hle

/-!
### 6. Todo Natural m ≥ 2 Possui um Divisor Primo (Hefez, Seção 2.1)
Conteúdo construtivo do Teorema Fundamental (existência, Dia 06): a testemunha
é `minFac m`, obtida por busca finita, sem lei do terceiro excluído.
-/
theorem exists_prime_dvd (m : Nat) (hm : 2 ≤ m) : ∃ p, IsPrime p ∧ p ∣ m :=
  ⟨minFac m, minFac_prime m hm, (minFac_spec m hm).2.1⟩

/-!
### 7. O Fatorial Absorve Todo Natural p ≤ n
-/
theorem dvd_fact (p : Nat) (hp : 1 ≤ p) : ∀ n, p ≤ n → p ∣ fact n := by
  intro n
  induction n with
  | zero => intro hle; exfalso; omega
  | succ n ih =>
    intro hle
    cases Nat.lt_or_ge p (n + 1) with
    | inl hlt =>
      have hd : p ∣ fact n := ih (by omega)
      have hmid : fact n ∣ fact (n + 1) := ⟨n + 1, Nat.mul_comm (n + 1) (fact n)⟩
      exact Nat.dvd_trans hd hmid
    | inr hge =>
      have hpe : p = n + 1 := by omega
      subst hpe
      exact Nat.dvd_mul_right (n + 1) (fact n)

/-!
### 8. Lema do Absurdo de Euclides (Hefez, pág. 40, Problema 1.21)
Se um primo p divide simultaneamente a e a + 1, então p divide 1 —
impossível para p ≥ 2.
-/
theorem prime_dvd_consecutive (p a : Nat) (h1 : p ∣ a + 1) (h2 : p ∣ a) : p ∣ 1 := by
  obtain ⟨x, hx⟩ := h1
  obtain ⟨y, hy⟩ := h2
  have e1 : p * x = a + 1 := hx.symm
  have e2 : p * y = a := hy.symm
  refine ⟨x - y, ?_⟩
  cases Nat.lt_or_ge x y with
  | inl hxy =>
    -- x < y é impossível: p * x = a + 1 > a = p * y exigiria p * x ≤ p * y.
    exfalso
    have hle : x * p ≤ y * p := Nat.mul_le_mul_right p (by omega)
    rw [Nat.mul_comm p x] at e1
    rw [Nat.mul_comm p y] at e2
    omega
  | inr hxy =>
    -- x ≥ y: escreva x = y + d; então p * d = 1 é a testemunha procurada.
    obtain ⟨d, hd⟩ : ∃ d, x = y + d := ⟨x - y, by omega⟩
    subst hd
    have hdy : y + d - y = d := by omega
    rw [hdy]
    have e1' : p * y + p * d = a + 1 := by rw [← Nat.left_distrib p y d]; exact e1
    omega

/-!
### 9. Teorema de Euclides — Infinitude Construtiva dos Primos (Hefez, Cap. 2.4)
"Para todo n ∈ ℕ existe um número primo p > n."

Demonstração (construção de Euclides, Hefez pág. 40):
Seja m = n! + 1 ≥ 2. Pela Seção 6, m possui um divisor primo p.
Se p ≤ n, então p ∣ n! (Seção 7) e p ∣ n! + 1, logo p ∣ 1 pelo lema do
absurdo — contradizendo p ≥ 2. Portanto p > n. ∎
-/
theorem hefez_euclid_infinitude_primes (n : Nat) : ∃ p, IsPrime p ∧ n < p := by
  have hfact : 1 ≤ fact n := fact_pos n
  have hm : 2 ≤ fact n + 1 := by omega
  obtain ⟨p, hp_prime, hp_dvd⟩ := exists_prime_dvd (fact n + 1) hm
  have hp_ge2 : 2 ≤ p := hp_prime.1
  have hp_ge1 : 1 ≤ p := by omega
  refine ⟨p, hp_prime, ?_⟩
  cases Nat.lt_or_ge p n with
  | inl hpn =>
    exfalso
    have hp_dvd_fact : p ∣ fact n := dvd_fact p hp_ge1 n (Nat.le_of_lt hpn)
    have hp1 : p ∣ 1 := prime_dvd_consecutive p (fact n) hp_dvd hp_dvd_fact
    have hple : p ≤ 1 := Nat.le_of_dvd (by decide) hp1
    omega
  | inr hnp =>
    cases Nat.lt_or_ge n p with
    | inl h => exact h
    | inr hpn2 =>
      exfalso
      have hp_dvd_fact : p ∣ fact n := dvd_fact p hp_ge1 n hpn2
      have hp1 : p ∣ 1 := prime_dvd_consecutive p (fact n) hp_dvd hp_dvd_fact
      have hple : p ≤ 1 := Nat.le_of_dvd (by decide) hp1
      omega

/-!
### 10. Corolário: Inexistência de Cota Superior para os Primos
Formulação por redução ao absurdo de Hefez (pág. 40): os primos não podem
ser enumerados por uma lista finita, pois nenhuma cota L majora todos eles.
-/
theorem hefez_primes_unbounded : ¬ ∃ L : Nat, ∀ p : Nat, IsPrime p → p ≤ L := by
  intro h
  obtain ⟨L, hL⟩ := h
  obtain ⟨p, hp, hlt⟩ := hefez_euclid_infinitude_primes L
  have hle := hL p hp
  omega

/-!
### 11. Testemunha Computacional de Euclides
`euclidPrime n` = menor fator primo de n! + 1 — sempre um primo > n.
Sequência dos números de Euclides (OEIS A006862): 2, 3, 7, 25, 121, 721, 5041...
-/
def euclidPrime (n : Nat) : Nat := minFac (fact n + 1)

#eval (euclidPrime 1, euclidPrime 2, euclidPrime 3, euclidPrime 4, euclidPrime 5, euclidPrime 6)
#eval euclidPrime 7
#eval (minFac 360, minFac 721, minFac 5041)

example : euclidPrime 1 = 2 := by decide
example : euclidPrime 2 = 3 := by decide
example : euclidPrime 3 = 7 := by decide
example : euclidPrime 4 = 5 := by decide
example : euclidPrime 5 = 11 := by decide
example : euclidPrime 6 = 7 := by decide
example : euclidPrime 7 = 71 := by decide
example : minFac 360 = 2 := by decide

end Dia08EuclidInfinitude
