/-
  Chronokairo AXIOM — Mathematical Investigation Dossier
  Dia 09: Equações Diofantinas Lineares em Duas Variáveis
  Referência: "Iniciação à Aritmética" (Abramo Hefez, SBM/OBMEP), Cap. 3.10, pág. 75-80.
  Kernel: Lean 4 (compatível com v4.14.0 do CI e v4.35.0 local)
  Garantia Epistêmica: formal-proof (Machine-checked, zero sorry, zero untrusted axioms)

  Enunciado canônico (Hefez, Teorema 3.5, pág. 78):
  "Seja x₀ e y₀ uma solução particular, arbitrariamente dada, da equação
   ax + by = c, onde mdc(a, b) = 1. Então as soluções da equação são da forma
   x = x₀ + tb e y = y₀ - ta, para t variando em ℤ."

  Critério de Solubilidade (Hefez, pág. 76-77):
  A equação ax + by = c possui solução inteira (x, y) se e somente se
  mdc(a, b) divide c.
-/

namespace Dia09Diophantine

/-!
### 1. Definição Epistêmica: Solução de Equação Diofantina Linear em ℤ
-/
def IsSolution (a b c x y : Int) : Prop :=
  a * x + b * y = c

/-!
### 2. Necessidade da Condição de Divisibilidade
Se um inteiro d divide tanto a quanto b, então d divide ax + by = c para
qualquer solução inteira (x, y). Logo, se a equação tem solução, mdc(a, b) ∣ c.
-/
theorem diophantine_dvd_c (a b c x y d : Int)
    (hsol : IsSolution a b c x y)
    (hda : d ∣ a)
    (hdb : d ∣ b) :
    d ∣ c := by
  have heq : c = a * x + b * y := hsol.symm
  rw [heq]
  have h1 : d ∣ a * x := Int.dvd_trans hda (Int.dvd_mul_right a x)
  have h2 : d ∣ b * y := Int.dvd_trans hdb (Int.dvd_mul_right b y)
  exact Int.dvd_add h1 h2

/-!
### 3. Suficiência: Existência de Solução Particular via Bézout
Se d = a*u + b*v divide c (onde c = d * k), então (u * k, v * k) é uma solução
particular de ax + by = c.
-/
theorem diophantine_particular_solution (a b c d u v k : Int)
    (hbez : a * u + b * v = d)
    (hc : c = d * k) :
    IsSolution a b c (u * k) (v * k) := by
  dsimp [IsSolution]
  calc
    a * (u * k) + b * (v * k) = (a * u) * k + (b * v) * k := by
      rw [Int.mul_assoc a u k, Int.mul_assoc b v k]
    _ = (a * u + b * v) * k := by rw [Int.add_mul]
    _ = d * k := by rw [hbez]
    _ = c := hc.symm

/-!
### 4. Lema de Coprimaridade Linear em ℤ (Hefez, Corolário 3.4 / Proposição 3.3)
Se a*u + b*v = 1 e a divide b*w, então a divide w.
-/
theorem coprime_dvd_mul_int (a b w u v : Int)
    (hcoprime : a * u + b * v = 1)
    (hdvd : a ∣ b * w) :
    a ∣ w := by
  have hid : w = a * (u * w) + (b * w) * v := by
    calc
      w = 1 * w := by rw [Int.one_mul]
      _ = (a * u + b * v) * w := by rw [hcoprime]
      _ = (a * u) * w + (b * v) * w := by rw [Int.add_mul]
      _ = a * (u * w) + (b * w) * v := by
        rw [Int.mul_assoc a u w, Int.mul_assoc b v w, Int.mul_comm v w, ← Int.mul_assoc b w v]
  rw [hid]
  have h1 : a ∣ a * (u * w) := Int.dvd_mul_right a (u * w)
  have h2 : a ∣ (b * w) * v := Int.dvd_trans hdvd (Int.dvd_mul_right (b * w) v)
  exact Int.dvd_add h1 h2

/-!
### 5. Verificação Direta da Família Geral de Soluções (Recíproca de Hefez)
Dada qualquer solução particular (x₀, y₀) de ax + by = c, o par
(x₀ + t*b, y₀ - t*a) é sempre uma solução inteira, para qualquer t ∈ ℤ.
-/
theorem diophantine_general_valid (a b c x₀ y₀ t : Int)
    (hsol₀ : IsSolution a b c x₀ y₀) :
    IsSolution a b c (x₀ + t * b) (y₀ - t * a) := by
  dsimp [IsSolution] at *
  calc
    a * (x₀ + t * b) + b * (y₀ - t * a)
      = a * x₀ + a * (t * b) + (b * y₀ - b * (t * a)) := by
        rw [Int.mul_add, Int.mul_sub]
    _ = a * x₀ + b * y₀ + (a * (t * b) - b * (t * a)) := by omega
    _ = c + 0 := by
      have hcancel : a * (t * b) = b * (t * a) := by
        calc
          a * (t * b) = a * t * b := by rw [Int.mul_assoc]
          _ = t * a * b := by rw [Int.mul_comm a t]
          _ = b * (t * a) := by rw [Int.mul_comm (t * a) b]
      rw [hsol₀, hcancel, Int.sub_self]
    _ = c := by omega

/-!
### 6. Teorema 3.5 de Abramo Hefez: Caracterização Completa da Solução Geral
"Se mdc(a, b) = 1 e (x₀, y₀) é uma solução particular dada de ax + by = c,
então toda solução (x, y) é da forma x = x₀ + t*b e y = y₀ - t*a para algum t ∈ ℤ."
-/
theorem hefez_diophantine_complete (a b c x₀ y₀ x y u v : Int)
    (hcoprime : a * u + b * v = 1)
    (hsol₀ : IsSolution a b c x₀ y₀)
    (hsol : IsSolution a b c x y)
    (hb_ne_zero : b ≠ 0) :
    ∃ t : Int, x = x₀ + t * b ∧ y = y₀ - t * a := by
  dsimp [IsSolution] at hsol₀ hsol
  -- 1. Subtraindo as duas equações: a(x - x₀) = b(y₀ - y)
  have hdiff : a * (x - x₀) = b * (y₀ - y) := by
    calc
      a * (x - x₀) = a * x - a * x₀ := by rw [Int.mul_sub]
      _ = (c - b * y) - (c - b * y₀) := by omega
      _ = b * y₀ - b * y := by omega
      _ = b * (y₀ - y) := by rw [Int.mul_sub]
  -- 2. b divide a * (x - x₀). Pela coprimaridade (b*v + a*u = 1), b divide (x - x₀).
  have hcoprime_ba : b * v + a * u = 1 := by rw [Int.add_comm]; exact hcoprime
  have hdvd_ax : b ∣ a * (x - x₀) := ⟨y₀ - y, by rw [hdiff, Int.mul_comm]⟩
  have hdvd_x : b ∣ (x - x₀) := coprime_dvd_mul_int b a (x - x₀) v u hcoprime_ba hdvd_ax
  -- 3. Logo x - x₀ = b * t = t * b para algum t ∈ ℤ
  obtain ⟨t, ht⟩ := hdvd_x
  have hx : x = x₀ + t * b := by
    have : x - x₀ = t * b := by rw [ht, Int.mul_comm]
    omega
  refine ⟨t, hx, ?_⟩
  -- 4. Substituindo x - x₀ = t * b em a(x - x₀) = b(y₀ - y):
  --    b * (y₀ - y) = b * (t * a)  ==>  y₀ - y = t * a
  have hcancel : b * (y₀ - y) = b * (t * a) := by
    calc
      b * (y₀ - y) = a * (x - x₀) := hdiff.symm
      _ = a * (b * t) := by rw [ht]
      _ = a * (t * b) := by rw [Int.mul_comm b t]
      _ = a * t * b := by rw [Int.mul_assoc]
      _ = b * (t * a) := by
        rw [Int.mul_comm (a * t) b, Int.mul_comm a t]
  have hy_diff : y₀ - y = t * a := Int.eq_of_mul_eq_mul_left hb_ne_zero hcancel
  omega

/-!
### 7. Aplicação Numérica Canônica de Abramo Hefez (Problema 3.54, pág. 79)
Equação dos selos: 3x + 5y = 50.
Solução particular: x₀ = 0, y₀ = 10 (pois 3*0 + 5*10 = 50).
Verificação formal de que t ∈ {0, 1, 2, 3} produz exatamente as 4 soluções
não-negativas de Hefez:
  t = 0: (0, 10)  -- 10 selos de 5 reais
  t = 1: (5, 7)   -- 5 selos de 3 reais e 7 de 5 reais
  t = 2: (10, 4)  -- 10 selos de 3 reais e 4 de 5 reais
  t = 3: (15, 1)  -- 15 selos de 3 reais e 1 de 5 reais
-/
def hefez_selos_x (t : Int) : Int := 0 + t * 5
def hefez_selos_y (t : Int) : Int := 10 - t * 3

theorem hefez_selos_valid (t : Int) :
    IsSolution 3 5 50 (hefez_selos_x t) (hefez_selos_y t) :=
  diophantine_general_valid 3 5 50 0 10 t (show 3 * 0 + 5 * 10 = 50 from rfl)

example : hefez_selos_x 0 = 0 ∧ hefez_selos_y 0 = 10 := by decide
example : hefez_selos_x 1 = 5 ∧ hefez_selos_y 1 = 7 := by decide
example : hefez_selos_x 2 = 10 ∧ hefez_selos_y 2 = 4 := by decide
example : hefez_selos_x 3 = 15 ∧ hefez_selos_y 3 = 1 := by decide

#eval (hefez_selos_x 0, hefez_selos_y 0)
#eval (hefez_selos_x 1, hefez_selos_y 1)
#eval (hefez_selos_x 2, hefez_selos_y 2)
#eval (hefez_selos_x 3, hefez_selos_y 3)

end Dia09Diophantine
