/-
  Chronokairo AXIOM — Mathematical Investigation Dossier
  Dia 04: Identidade de Bézout e Algoritmo Estendido de Euclides
  Referência: "Iniciação à Aritmética" (Abramo Hefez, SBM/OBMEP), Seção 3.8 e 3.9, pág. 66-74.
  Kernel: Lean 4 (version 4.35.0)
  Garantia Epistêmica: formal-proof (Machine-checked, zero sorry, zero untrusted axioms)
-/

namespace Dia04Bezout

/-!
### 1. Algoritmo Estendido de Euclides Construtivo (XGCD)
Implementação construtiva do algoritmo que gera os coeficientes inteiros de Bézout
seguindo a tabela de retrosubstituição de Euclides descrita por Abramo Hefez.
-/
def xgcd : Nat → Nat → Int × Int
  | 0, _ => (0, 1)
  | a + 1, b =>
    have : b % (a + 1) < a + 1 := Nat.mod_lt b (Nat.succ_pos a)
    let (s, t) := xgcd (b % (a + 1)) (a + 1)
    (t - s * ((b / (a + 1) : Nat) : Int), s)
termination_by a _ => a

-- Verificação numérica do exemplo canônico da página 69 de Abramo Hefez: mdc(372, 162) = 6
#eval xgcd 372 162 -- (-10, 23) -> 372 * (-10) + 162 * 23 = -3720 + 3726 = 6

/-!
### 2. Lema Auxiliar Algébrico de Retrosubstituição
Demonstra que a reorganização dos coeficientes na indução euclidiana preserva a identidade.
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
### 3. Teorema 3.3 (Identidade de Bézout - Abramo Hefez, pág. 69)
"Dados inteiros a e b quaisquer, existem inteiros x e y tais que a*x + b*y = mdc(a, b)."
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
### 4. Corolário Fundamental (Abramo Hefez, Seção 3.9, pág. 70)
"Se d divide a e d divide b, então d divide mdc(a, b)."
Demonstrado como consequência direta da identidade linear de Bézout.
-/
theorem hefez_common_divisor_divides_gcd (d : Int) (a b : Nat)
    (x y : Int) (hbez : (a : Int) * x + (b : Int) * y = (Nat.gcd a b : Int))
    (hda : d ∣ (a : Int)) (hdb : d ∣ (b : Int)) :
    d ∣ (Nat.gcd a b : Int) := by
  rw [← hbez]
  have h1 : d ∣ (a : Int) * x := Int.dvd_trans hda (Int.dvd_mul_right (a : Int) x)
  have h2 : d ∣ (b : Int) * y := Int.dvd_trans hdb (Int.dvd_mul_right (b : Int) y)
  exact Int.dvd_add h1 h2

end Dia04Bezout
