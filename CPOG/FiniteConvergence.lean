import Mathlib
import CPOG.Convergence

namespace CPOG.FiniteConvergence

open CPOG.Convergence

universe uN
variable {N : Type uN}

noncomputable def reachSet [Fintype N]
    (E : N → N → Prop) (y : N) (k : Nat) : Finset N := by
  classical
  exact Finset.univ.filter (fun x => ReachWithin E k y x)

@[simp]
theorem mem_reachSet_iff [Fintype N]
    (E : N → N → Prop) (y x : N) (k : Nat) :
    x ∈ reachSet E y k ↔ ReachWithin E k y x := by
  classical
  simp [reachSet]

theorem reachSet_subset_next [Fintype N]
    (E : N → N → Prop) (y : N) (k : Nat) :
    reachSet E y k ⊆ reachSet E y (k + 1) := by
  classical
  intro x hx
  exact (mem_reachSet_iff E y x (k + 1)).2
    (reachWithin_mono E ((mem_reachSet_iff E y x k).1 hx))

/-- Once the finite reachable-set iteration stops growing, it never grows again. -/
theorem reachSet_eq_next_step [Fintype N]
    (E : N → N → Prop) (y : N) (k : Nat)
    (h : reachSet E y k = reachSet E y (k + 1)) :
    reachSet E y (k + 1) = reachSet E y (k + 2) := by
  classical
  apply Finset.ext
  intro x
  simp only [mem_reachSet_iff]
  constructor
  · exact reachWithin_mono E
  · intro hx
    rcases hx with hx | ⟨z, hzx, hz⟩
    · exact hx
    · have hzmem : z ∈ reachSet E y (k + 1) :=
        (mem_reachSet_iff E y z (k + 1)).2 hz
      have hzmem0 : z ∈ reachSet E y k := by
        rw [h]
        exact hzmem
      have hz0 : ReachWithin E k y z :=
        (mem_reachSet_iff E y z k).1 hzmem0
      exact Or.inr ⟨z, hzx, hz0⟩

/-- Equality at one round persists at every later round. -/
theorem reachSet_eq_next_persists [Fintype N]
    (E : N → N → Prop) (y : N) {k : Nat}
    (h : reachSet E y k = reachSet E y (k + 1)) :
    ∀ m, reachSet E y (k + m) = reachSet E y (k + m + 1) := by
  intro m
  induction m with
  | zero =>
      simpa using h
  | succ m ih =>
      have hnext := reachSet_eq_next_step E y (k + m) ih
      convert hnext using 1 <;> omega

/-- Reachability is monotone in the allowed path length. -/
theorem reachWithin_mono_le
    (E : N → N → Prop) {k m : Nat} {y x : N}
    (hkm : k ≤ m) (h : ReachWithin E k y x) :
    ReachWithin E m y x := by
  obtain ⟨d, rfl⟩ := Nat.exists_eq_add_of_le hkm
  clear hkm
  induction d with
  | zero => simpa
  | succ d ih =>
      have hs := reachWithin_mono E ih
      convert hs using 1 <;> omega

/-- Cardinality growth across a sequence of strict finite-set refinements. -/
theorem card_add_le_of_strict_chain [Fintype N]
    (s : Nat → Finset N) :
    ∀ m,
      (∀ k, k < m → s k ⊂ s (k + 1)) →
      (s 0).card + m ≤ (s m).card := by
  intro m
  induction m with
  | zero =>
      intro _
      simp
  | succ m ih =>
      intro hstrict
      have hprev : (s 0).card + m ≤ (s m).card :=
        ih (fun k hk => hstrict k (Nat.lt_trans hk (Nat.lt_succ_self m)))
      have hss : s m ⊂ s (m + 1) := hstrict m (Nat.lt_succ_self m)
      have hcard : (s m).card < (s (m + 1)).card := Finset.card_lt_card hss
      omega

/-- The zero-round reachable set from a source has exactly one element. -/
theorem card_reachSet_zero [Fintype N]
    (E : N → N → Prop) (y : N) :
    (reachSet E y 0).card = 1 := by
  classical
  have hset : reachSet E y 0 = {y} := by
    ext x
    simp [reachSet, ReachWithin, eq_comm]
  simp [hset]

/--
For a finite nonempty state space, the reachable-set iteration from any source has stabilized
by round |N|-1. This is the combinatorial core of the sharp propagation bound.
-/
theorem reachSet_fixed_card_sub_one
    [Fintype N] [Nonempty N]
    (E : N → N → Prop) (y : N) :
    reachSet E y (Fintype.card N - 1) =
      reachSet E y (Fintype.card N) := by
  classical
  let n := Fintype.card N
  have hnpos : 0 < n := by
    dsimp [n]
    exact Fintype.card_pos_iff.mpr inferInstance
  by_contra hneq
  have hstrict : ∀ k, k < n → reachSet E y k ⊂ reachSet E y (k + 1) := by
    intro k hk
    have hsub := reachSet_subset_next E y k
    refine (Finset.ssubset_iff_subset_ne).2 ⟨hsub, ?_⟩
    intro heq
    have hpersist := reachSet_eq_next_persists E y heq (n - 1 - k)
    have hfinal : reachSet E y (n - 1) = reachSet E y n := by
      convert hpersist using 1 <;> omega
    exact hneq (by simpa [n] using hfinal)
  have hgrowth : (reachSet E y 0).card + n ≤ (reachSet E y n).card :=
    card_add_le_of_strict_chain (fun k => reachSet E y k) n hstrict
  have hzero : (reachSet E y 0).card = 1 := card_reachSet_zero E y
  have hupper : (reachSet E y n).card ≤ n := by
    dsimp [n]
    exact Finset.card_le_univ _
  omega

/-- Every reachable pair in a finite nonempty graph has a witness within |N|-1 edges. -/
theorem reachBoundedBy_card_sub_one
    [Fintype N] [Nonempty N]
    (E : N → N → Prop) :
    ReachBoundedBy E (Fintype.card N - 1) := by
  classical
  intro y x hreach
  rcases hreach with ⟨k, hk⟩
  let K := Fintype.card N - 1
  by_cases hle : k ≤ K
  · exact reachWithin_mono_le E hle hk
  · have hfix : reachSet E y K = reachSet E y (K + 1) := by
      have hcard := reachSet_fixed_card_sub_one E y
      have hpos : 0 < Fintype.card N := Fintype.card_pos_iff.mpr inferInstance
      convert hcard using 1 <;> dsimp [K] <;> omega
    have hKk : K ≤ k := Nat.le_of_lt (Nat.lt_of_not_ge hle)
    obtain ⟨d, hd⟩ := Nat.exists_eq_add_of_le hKk
    subst k
    have hpersist := reachSet_eq_next_persists E y hfix
    have hall : ∀ m, reachSet E y K = reachSet E y (K + m) := by
      intro m
      induction m with
      | zero => simp
      | succ m ih =>
          have hstep := hpersist m
          calc
            reachSet E y K = reachSet E y (K + m) := ih
            _ = reachSet E y (K + m + 1) := hstep
            _ = reachSet E y (K + (m + 1)) := by congr 2 <;> omega
    have hxmem : x ∈ reachSet E y (K + d) :=
      (mem_reachSet_iff E y x (K + d)).2 hk
    have hxK : x ∈ reachSet E y K := by
      rw [hall d]
      exact hxmem
    exact (mem_reachSet_iff E y x K).1 hxK

/-- Sharp finite convergence bound for one-bit support propagation. -/
theorem supportIter_fixed_card_sub_one
    [Fintype N] [Nonempty N]
    (E : N → N → Prop) (S : N → Prop) :
    SupportIter E S (Fintype.card N - 1) =
      SupportIter E S (Fintype.card N) := by
  have hbound := reachBoundedBy_card_sub_one E
  have h := supportIter_fixed_of_reachBound E S (Fintype.card N - 1) hbound
  have hpos : 0 < Fintype.card N := Fintype.card_pos_iff.mpr inferInstance
  convert h using 1 <;> omega

/-- Sharp finite convergence bound for two-bit FDE propagation. -/
theorem fdeIter_fixed_card_sub_one
    [Fintype N] [Nonempty N]
    (E : N → N → Prop) (σ : PropEvidence N) :
    FDEIter E σ (Fintype.card N - 1) =
      FDEIter E σ (Fintype.card N) := by
  have hbound := reachBoundedBy_card_sub_one E
  have h := fdeIter_fixed_of_reachBound E σ (Fintype.card N - 1) hbound
  have hpos : 0 < Fintype.card N := Fintype.card_pos_iff.mpr inferInstance
  convert h using 1 <;> omega

end CPOG.FiniteConvergence
