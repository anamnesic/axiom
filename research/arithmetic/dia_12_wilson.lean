/-
  Chronokairo AXIOM — Dia 12: Teorema de Wilson
  Referência: Brochero et al., Um Passeio pelos Primos, §1.6,
  Lema 1.33 e Teorema 1.34, pp. 43–44 (PDF pp. 56–57).
  Enunciado: para p ≥ 2, p é primo ↔ p ∣ ((p-1)! + 1).
  Prova autônoma: Bézout, inversos e pareamento; apenas Lean Init.
-/
import Init.Data.Nat.Basic
import Init.Data.Int.Basic
import Init.Data.List.Lemmas
import Init.Data.List.Erase

namespace Dia12Wilson

def IsPrime (p : Nat) : Prop :=
  p ≥ 2 ∧ ∀ d : Nat, d ∣ p → d = 1 ∨ d = p

def Cong (p : Nat) (a b : Int) : Prop := (p : Int) ∣ a - b

theorem bezout_algebra (m t s q r : Int) :
    m * (t - s * q) + (m * q + r) * s = r * s + m * t := by
  rw [Int.mul_sub, Int.add_mul]
  have h : m * (s * q) = (m * q) * s := by
    rw [Int.mul_assoc, Int.mul_comm s q, ← Int.mul_assoc]
  rw [h]
  omega

theorem bezout (a b : Nat) :
    ∃ x y : Int, (a : Int) * x + (b : Int) * y = (Nat.gcd a b : Int) := by
  induction a, b using Nat.gcd.induction with
  | H0 n => exact ⟨0, 1, by simp [Nat.gcd_zero_left]⟩
  | H1 m n hm ih =>
    obtain ⟨s, t, hst⟩ := ih
    refine ⟨t - s * ((n / m : Nat) : Int), s, ?_⟩
    have heuc : (n : Int) = (m : Int) * ((n / m : Nat) : Int) + ((n % m : Nat) : Int) :=
      congrArg Int.ofNat (Nat.div_add_mod n m).symm
    rw [heuc, bezout_algebra, hst]
    exact congrArg Int.ofNat (Nat.gcd_rec m n).symm

theorem coprime_cancel (a b c x y : Int)
    (hb : a * x + b * y = 1) (hd : a ∣ b * c) : a ∣ c := by
  have hid : c = a * (x * c) + (b * c) * y := by
    calc
      c = 1 * c := (Int.one_mul c).symm
      _ = (a * x + b * y) * c := by rw [hb]
      _ = a * (x * c) + (b * c) * y := by
        rw [Int.add_mul, Int.mul_assoc a x c, Int.mul_assoc b y c,
          Int.mul_comm y c, ← Int.mul_assoc b c y]
  rw [hid]
  exact Int.dvd_add (Int.dvd_mul_right _ _) (Int.dvd_trans hd (Int.dvd_mul_right _ _))

theorem prime_gcd (p a : Nat) (hp : IsPrime p) (ha : 0 < a) (hlt : a < p) :
    Nat.gcd p a = 1 := by
  cases hp.2 (Nat.gcd p a) (Nat.gcd_dvd_left p a) with
  | inl h => exact h
  | inr h =>
    have hd := Nat.gcd_dvd_right p a
    rw [h] at hd
    have := Nat.le_of_dvd ha hd
    omega

theorem euclid (p a b : Nat) (hp : IsPrime p) (hd : p ∣ a * b) : p ∣ a ∨ p ∣ b := by
  cases hp.2 (Nat.gcd p a) (Nat.gcd_dvd_left p a) with
  | inl hg =>
    right
    obtain ⟨x, y, hb⟩ := bezout p a
    rw [hg] at hb
    exact Int.ofNat_dvd.1 (coprime_cancel (p : Int) (a : Int) (b : Int) x y hb
      (Int.ofNat_dvd.2 hd))
  | inr hg =>
    left
    have h := Nat.gcd_dvd_right p a
    rw [hg] at h
    exact h

theorem cong_refl (p : Nat) (a : Int) : Cong p a a := by
  exact ⟨0, by omega⟩

theorem cong_symm {p : Nat} {a b : Int} (h : Cong p a b) : Cong p b a := by
  obtain ⟨k, hk⟩ := h
  exact ⟨-k, by rw [Int.mul_neg]; omega⟩

theorem cong_trans {p : Nat} {a b c : Int} (h : Cong p a b) (g : Cong p b c) :
    Cong p a c := by
  obtain ⟨k, hk⟩ := h
  obtain ⟨l, hl⟩ := g
  exact ⟨k + l, by rw [Int.mul_add]; omega⟩

theorem cong_mul {p : Nat} {a b c d : Int} (h : Cong p a b) (g : Cong p c d) :
    Cong p (a * c) (b * d) := by
  obtain ⟨k, hk⟩ := h
  obtain ⟨l, hl⟩ := g
  refine ⟨k * c + b * l, ?_⟩
  have heq : a * c - b * d = (a - b) * c + b * (c - d) := by
    rw [Int.sub_mul, Int.mul_sub]; omega
  rw [heq, hk, hl, Int.mul_add, Int.mul_assoc, Int.mul_left_comm b]

theorem mod_cong (p a : Nat) : Cong p (a : Int) ((a % p : Nat) : Int) := by
  refine ⟨(a / p : Nat), ?_⟩
  have h : (p : Int) * ((a / p : Nat) : Int) + ((a % p : Nat) : Int) = (a : Int) :=
    congrArg Int.ofNat (Nat.div_add_mod a p)
  omega

theorem small_cong {p a b : Nat} (ha : a < p) (hb : b < p)
    (h : Cong p (a : Int) (b : Int)) : a = b := by
  obtain ⟨k, hk⟩ := h
  have h1 : (p : Int) * k < (p : Int) * 1 := by omega
  have h2 : (p : Int) * (-1) < (p : Int) * k := by
    rw [Int.mul_neg, Int.mul_one]; omega
  have := Int.lt_of_mul_lt_mul_left h1 (by omega : (0 : Int) ≤ p)
  have := Int.lt_of_mul_lt_mul_left h2 (by omega : (0 : Int) ≤ p)
  have : k = 0 := by omega
  rw [this, Int.mul_zero] at hk
  omega

theorem inverse_exists (p a : Nat) (hp : IsPrime p) (ha : 0 < a) (hlt : a < p) :
    ∃ b : Nat, 0 < b ∧ b < p ∧ Cong p ((a : Int) * b) 1 := by
  obtain ⟨x, y, hb⟩ := bezout p a
  rw [prime_gcd p a hp ha hlt] at hb
  have hp2 := hp.1
  have hex : ∃ n : Nat, Cong p ((a : Int) * n) 1 := by
    by_cases hy : 0 ≤ y
    · refine ⟨y.toNat, ?_⟩
      rw [Int.toNat_of_nonneg hy]
      exact ⟨-x, by rw [Int.mul_neg]; omega⟩
    · let z := y + (p : Int) * (-y)
      have hmul : (1 : Int) * (-y) ≤ (p : Int) * (-y) :=
        Int.mul_le_mul_of_nonneg_right (by omega) (by omega)
      have hz : 0 ≤ z := by dsimp [z]; rw [Int.one_mul] at hmul; omega
      refine ⟨z.toNat, ?_⟩
      rw [Int.toNat_of_nonneg hz]
      refine ⟨-x + (a : Int) * (-y), ?_⟩
      dsimp [z]
      rw [Int.mul_add, Int.mul_add, Int.mul_neg (p : Int) x,
        Int.mul_left_comm (a : Int) (p : Int)]
      omega
  obtain ⟨n, hn⟩ := hex
  have hr : Cong p ((a : Int) * ((n % p : Nat) : Int)) 1 :=
    cong_trans (cong_symm (cong_mul (cong_refl p (a : Int)) (mod_cong p n))) hn
  refine ⟨n % p, ?_, Nat.mod_lt n (by omega), hr⟩
  by_cases hz : 0 < n % p
  · exact hz
  have hn0 : n % p = 0 := by omega
  rw [hn0] at hr
  change Cong p ((a : Int) * 0) 1 at hr
  rw [Int.mul_zero] at hr
  have heq := small_cong (by omega : 0 < p) (by omega : 1 < p) hr
  omega

theorem inverse_unique (p a b c : Nat) (hp : IsPrime p) (ha : 0 < a) (hlt : a < p)
    (hb : b < p) (hc : c < p) (hab : Cong p ((a : Int) * b) 1)
    (hac : Cong p ((a : Int) * c) 1) : b = c := by
  obtain ⟨x, y, hbez⟩ := bezout p a
  rw [prime_gcd p a hp ha hlt] at hbez
  apply small_cong hb hc
  apply coprime_cancel (p : Int) (a : Int) ((b : Int) - c) x y hbez
  have hd := Int.dvd_sub hab hac
  have heq : (a : Int) * b - 1 - ((a : Int) * c - 1) = (a : Int) * ((b : Int) - c) := by
    rw [Int.mul_sub]; omega
  rw [heq] at hd
  exact hd

theorem self_inverse (p a : Nat) (hp : IsPrime p) (ha : 0 < a) (hlt : a < p)
    (h : Cong p ((a : Int) * a) 1) : a = 1 ∨ a = p - 1 := by
  have heq : (((a - 1) * (a + 1) : Nat) : Int) = (a : Int) * a - 1 := by
    rw [Int.natCast_mul, Int.ofNat_sub (by omega : 1 ≤ a), Int.natCast_add]
    change ((a : Int) - 1) * ((a : Int) + 1) = (a : Int) * a - 1
    rw [Int.sub_mul, Int.mul_add, Int.one_mul, Int.mul_one]
    omega
  have hd : p ∣ (a - 1) * (a + 1) := Int.ofNat_dvd.1 (by rw [heq]; exact h)
  cases euclid p (a - 1) (a + 1) hp hd with
  | inl hd =>
    left
    by_cases he : a = 1
    · exact he
    · have := Nat.le_of_dvd (by omega : 0 < a - 1) hd
      omega
  | inr hd =>
    right
    have hh := Nat.le_of_dvd (by omega : 0 < a + 1) hd
    omega

def prod : List Nat → Nat
  | [] => 1
  | a :: l => a * prod l

theorem prod_erase (l : List Nat) (b : Nat) (hb : b ∈ l) :
    prod l = b * prod (l.erase b) := by
  induction l with
  | nil => simp at hb
  | cons a l ih =>
    by_cases hab : a = b
    · subst a
      simp [prod]
    · have hba : b ≠ a := Ne.symm hab
      have hbl : b ∈ l := (List.mem_cons.1 hb).resolve_left hba
      have he : (a :: l).erase b = a :: l.erase b := by
        simp [hab]
      rw [he]
      change a * prod l = b * (a * prod (l.erase b))
      rw [ih hbl, Nat.mul_left_comm]

/- Closed lists of distinct, non-self-inverse residues split into inverse pairs. -/
theorem paired_product (p : Nat) (hp : IsPrime p) (l : List Nat)
    (hn : l.Nodup) (hr : ∀ a ∈ l, 1 < a ∧ a < p - 1)
    (hclosed : ∀ a ∈ l, ∃ b ∈ l, Cong p ((a : Int) * b) 1) :
    Cong p (prod l : Int) 1 := by
  match l with
  | [] => exact cong_refl p 1
  | a :: l =>
    have hnd := List.nodup_cons.1 hn
    have har := hr a (by simp)
    obtain ⟨b, hbl, hab⟩ := hclosed a (by simp)
    have hbr := hr b hbl
    have hne : b ≠ a := by
      intro he
      rw [he] at hab
      cases self_inverse p a hp (by omega) (by omega) hab <;> omega
    have hbl' : b ∈ l := (List.mem_cons.1 hbl).resolve_left hne
    have hrest : ∀ c ∈ l.erase b, 1 < c ∧ c < p - 1 := by
      intro c hc
      exact hr c (List.mem_cons.2 (Or.inr (List.mem_of_mem_erase hc)))
    have hclose : ∀ c ∈ l.erase b, ∃ d ∈ l.erase b, Cong p ((c : Int) * d) 1 := by
      intro c hc
      have hcl := List.mem_of_mem_erase hc
      have hcr := hrest c hc
      obtain ⟨d, hd, hcd⟩ := hclosed c (List.mem_cons.2 (Or.inr hcl))
      have hdr := hr d hd
      have hca : c ≠ a := by intro he; subst c; exact hnd.1 hcl
      have hcb : c ≠ b := by
        intro he
        subst c
        exact (List.Nodup.not_mem_erase hnd.2) hc
      have hda : d ≠ a := by
        intro he
        subst d
        have hbc : Cong p ((a : Int) * c) 1 := by rw [Int.mul_comm]; exact hcd
        exact hcb (inverse_unique p a c b hp (by omega) (by omega) (by omega) (by omega) hbc hab)
      have hdb : d ≠ b := by
        intro he
        subst d
        have hba : Cong p ((b : Int) * a) 1 := by rw [Int.mul_comm]; exact hab
        have hbc : Cong p ((b : Int) * c) 1 := by rw [Int.mul_comm]; exact hcd
        exact hca (inverse_unique p b c a hp (by omega) (by omega) (by omega) (by omega) hbc hba)
      exact ⟨d, (List.mem_erase_of_ne hdb).2 ((List.mem_cons.1 hd).resolve_left hda), hcd⟩
    have ih := paired_product p hp (l.erase b) (hnd.2.erase b) hrest hclose
    have heq : prod (a :: l) = (a * b) * prod (l.erase b) := by
      change a * prod l = _
      rw [prod_erase l b hbl', Nat.mul_assoc]
    rw [heq, Int.natCast_mul, Int.natCast_mul]
    have h := cong_mul hab ih
    simpa using h
termination_by l.length
decreasing_by
  have := List.length_erase_of_mem hbl'
  simp only [List.length_cons]
  omega

def middle : Nat → List Nat
  | 0 => []
  | n + 1 => (n + 2) :: middle n

theorem mem_middle (n a : Nat) : a ∈ middle n ↔ 2 ≤ a ∧ a ≤ n + 1 := by
  induction n with
  | zero => simp [middle]; omega
  | succ n ih =>
    simp only [middle, List.mem_cons, ih]
    omega

theorem middle_nodup (n : Nat) : (middle n).Nodup := by
  induction n with
  | zero => simp [middle]
  | succ n ih =>
    apply List.nodup_cons.2
    exact ⟨by intro h; have := (mem_middle n (n + 2)).1 h; omega, ih⟩

def fact : Nat → Nat
  | 0 => 1
  | n + 1 => (n + 1) * fact n

theorem fact_middle (n : Nat) : fact (n + 1) = prod (middle n) := by
  induction n with
  | zero => rfl
  | succ n ih =>
    change (n + 2) * fact (n + 1) = (n + 2) * prod (middle n)
    rw [ih]

theorem minus_one_inverse (p : Nat) (hp : 2 ≤ p) :
    Cong p (((p - 1 : Nat) : Int) * ((p - 1 : Nat) : Int)) 1 := by
  refine ⟨(p : Int) - 2, ?_⟩
  rw [Int.ofNat_sub (by omega : 1 ≤ p)]
  change ((p : Int) - 1) * ((p : Int) - 1) - 1 = (p : Int) * ((p : Int) - 2)
  rw [Int.sub_mul, Int.mul_sub, Int.mul_one, Int.one_mul, Int.mul_sub]
  have ht : (p : Int) * 2 = (p : Int) + (p : Int) := by
    have h := Int.mul_add (p : Int) 1 1
    simpa using h
  rw [ht]
  omega

theorem wilson_forward (p : Nat) (hp : IsPrime p) : p ∣ fact (p - 1) + 1 := by
  have hp2 := hp.1
  by_cases he : p = 2
  · subst p
    decide
  have hp3 : 3 ≤ p := by omega
  let l := middle (p - 3)
  have hr : ∀ a ∈ l, 1 < a ∧ a < p - 1 := by
    intro a ha
    have := (mem_middle (p - 3) a).1 ha
    omega
  have hc : ∀ a ∈ l, ∃ b ∈ l, Cong p ((a : Int) * b) 1 := by
    intro a ha
    have har := hr a ha
    obtain ⟨b, hb0, hbp, hab⟩ := inverse_exists p a hp (by omega) (by omega)
    have hb1 : b ≠ 1 := by
      intro hb
      rw [hb] at hab
      change Cong p ((a : Int) * 1) 1 at hab
      rw [Int.mul_one] at hab
      have := small_cong (by omega : a < p) (by omega : 1 < p) hab
      omega
    have hbm : b ≠ p - 1 := by
      intro hb
      rw [hb] at hab
      have hba : Cong p (((p - 1 : Nat) : Int) * a) 1 := by
        rw [Int.mul_comm]; exact hab
      have heq := inverse_unique p (p - 1) a (p - 1) hp (by omega) (by omega)
        (by omega) (by omega) hba (minus_one_inverse p hp2)
      omega
    exact ⟨b, (mem_middle (p - 3) b).2 (by omega), hab⟩
  have hprod := paired_product p hp l (middle_nodup (p - 3)) hr hc
  have hf : fact (p - 1) = (p - 1) * prod l := by
    have h1 : p - 1 = (p - 2) + 1 := by omega
    have h2 : p - 2 = (p - 3) + 1 := by omega
    rw [h1, fact]
    rw [← h1, h2, fact_middle]
  have hminus : Cong p ((p - 1 : Nat) : Int) (-1) := by
    refine ⟨1, ?_⟩
    rw [Int.mul_one, Int.ofNat_sub (by omega : 1 ≤ p)]
    omega
  have h := cong_mul hminus hprod
  rw [← Int.natCast_mul, ← hf] at h
  have hd : (p : Int) ∣ ((fact (p - 1) + 1 : Nat) : Int) := by
    change (p : Int) ∣ (fact (p - 1) : Int) - (-1) * 1 at h
    rw [Int.mul_one] at h
    have heq : (fact (p - 1) : Int) - (-1) = ((fact (p - 1) + 1 : Nat) : Int) := by
      rw [Int.natCast_add]
      omega
    rw [heq] at h
    exact h
  exact Int.ofNat_dvd.1 hd

theorem dvd_fact (d n : Nat) (hd : 0 < d) (hle : d ≤ n) : d ∣ fact n := by
  induction n with
  | zero => omega
  | succ n ih =>
    by_cases he : d = n + 1
    · rw [he, fact]
      exact Nat.dvd_mul_right _ _
    · have hh := ih (by omega)
      rw [fact, Nat.mul_comm]
      exact Nat.dvd_trans hh (Nat.dvd_mul_right _ _)

theorem wilson_converse (p : Nat) (hp : 2 ≤ p) (hw : p ∣ fact (p - 1) + 1) :
    IsPrime p := by
  refine ⟨hp, ?_⟩
  intro d hd
  have hd0 : 0 < d := by
    by_cases he : d = 0
    · rw [he] at hd
      obtain ⟨k, hk⟩ := hd
      simp at hk
      omega
    · omega
  by_cases he : d = p
  · exact Or.inr he
  left
  have hle := Nat.le_of_dvd (by omega : 0 < p) hd
  have hdf := dvd_fact d (p - 1) hd0 (by omega)
  have hds := Nat.dvd_trans hd hw
  have hone : (d : Int) ∣ (1 : Int) := by
    have h := Int.dvd_sub (Int.ofNat_dvd.2 hds) (Int.ofNat_dvd.2 hdf)
    rw [Int.natCast_add] at h
    have heq : (fact (p - 1) : Int) + (1 : Int) - (fact (p - 1) : Int) = 1 := by omega
    change (d : Int) ∣ (fact (p - 1) : Int) + (1 : Int) - (fact (p - 1) : Int) at h
    rw [heq] at h
    exact h
  have := Nat.le_of_dvd (by decide : 0 < 1) (Int.ofNat_dvd.1 hone)
  omega

/- The lower bound is essential: at p = 1, divisibility alone holds. -/
theorem wilson_iff (p : Nat) (hp : 2 ≤ p) :
    IsPrime p ↔ p ∣ fact (p - 1) + 1 :=
  ⟨wilson_forward p, wilson_converse p hp⟩

theorem wilson_congruence (p : Nat) (hp : 2 ≤ p) :
    IsPrime p ↔ Cong p (fact (p - 1) : Int) (-1) := by
  have heq : Cong p (fact (p - 1) : Int) (-1) ↔ p ∣ fact (p - 1) + 1 := by
    unfold Cong
    have he : (fact (p - 1) : Int) - (-1) = ((fact (p - 1) + 1 : Nat) : Int) := by
      rw [Int.natCast_add]
      omega
    rw [he]
    exact Int.ofNat_dvd
  rw [heq]
  exact wilson_iff p hp

theorem wilson_two : 2 ∣ fact (2 - 1) + 1 := by decide
theorem wilson_seven : 7 ∣ fact (7 - 1) + 1 := by decide
theorem wilson_eleven : 11 ∣ fact (11 - 1) + 1 := by decide
theorem composite_four : ¬ (4 ∣ fact (4 - 1) + 1) := by decide
theorem composite_nine : ¬ (9 ∣ fact (9 - 1) + 1) := by decide
theorem boundary_one : 1 ∣ fact (1 - 1) + 1 ∧ ¬ IsPrime 1 := by
  constructor
  · decide
  · intro h; have := h.1; omega

end Dia12Wilson
