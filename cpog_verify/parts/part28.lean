
namespace CPOG.Convergence

universe uN
variable {N : Type uN}

/-- Synchronous inflationary support propagation iterated for an exact number of rounds. -/
def SupportIter (E : N → N → Prop) (S : N → Prop) : Nat → N → Prop
  | 0 => S
  | k + 1 => fun x => CPOG.DynamicSafety.SupportStep E (SupportIter E S k) x

/--
Reachability by a path of length at most k, with length zero represented by equality.
The recursion is aligned with incoming synchronous propagation.
-/
def ReachWithin (E : N → N → Prop) : Nat → N → N → Prop
  | 0, y, x => y = x
  | k + 1, y, x =>
      ReachWithin E k y x ∨
      ∃ z, E z x ∧ ReachWithin E k y z

theorem reachWithin_mono
    (E : N → N → Prop) {k : Nat} {y x : N}
    (h : ReachWithin E k y x) :
    ReachWithin E (k + 1) y x :=
  Or.inl h

/--
Closed form for synchronous support propagation:
after k rounds, x carries support exactly when some initially supported y reaches x
within at most k edges.
-/
theorem supportIter_iff_reachWithin
    (E : N → N → Prop) (S : N → Prop) :
    ∀ k x, SupportIter E S k x ↔
      ∃ y, ReachWithin E k y x ∧ S y := by
  intro k
  induction k with
  | zero =>
      intro x
      constructor
      · intro hx
        exact ⟨x, rfl, hx⟩
      · rintro ⟨y, hyx, hy⟩
        subst y
        exact hy
  | succ k ih =>
      intro x
      constructor
      · intro hx
        rcases hx with hx | ⟨z, hzx, hz⟩
        · rcases (ih x).mp hx with ⟨y, hyx, hy⟩
          exact ⟨y, Or.inl hyx, hy⟩
        · rcases (ih z).mp hz with ⟨y, hyz, hy⟩
          exact ⟨y, Or.inr ⟨z, hzx, hyz⟩, hy⟩
      · rintro ⟨y, hyx, hy⟩
        rcases hyx with hyx | ⟨z, hzx, hyz⟩
        · left
          exact (ih x).mpr ⟨y, hyx, hy⟩
        · right
          exact ⟨z, hzx, (ih z).mpr ⟨y, hyz, hy⟩⟩

/-- Global reachability, forgetting the number of rounds. -/
def Reachable (E : N → N → Prop) (y x : N) : Prop :=
  ∃ k, ReachWithin E k y x

/--
A numerical reach bound says every reachable pair already has a path within K rounds.
For finite identity-edge propagation, the paper's sharp |N|-1 theorem is obtained
once the corresponding finite-graph path-shortening lemma supplies this premise.
-/
def ReachBoundedBy (E : N → N → Prop) (K : Nat) : Prop :=
  ∀ y x, Reachable E y x → ReachWithin E K y x

theorem supportIter_fixed_of_reachBound
    (E : N → N → Prop) (S : N → Prop) (K : Nat)
    (hbound : ReachBoundedBy E K) :
    SupportIter E S K = SupportIter E S (K + 1) := by
  funext x
  apply propext
  constructor
  · intro hx
    rcases (supportIter_iff_reachWithin E S K x).mp hx with ⟨y, hyx, hy⟩
    exact (supportIter_iff_reachWithin E S (K + 1) x).mpr
      ⟨y, reachWithin_mono E hyx, hy⟩
  · intro hx
    rcases (supportIter_iff_reachWithin E S (K + 1) x).mp hx with ⟨y, hyx, hy⟩
    have hreach : Reachable E y x := ⟨K + 1, hyx⟩
    exact (supportIter_iff_reachWithin E S K x).mpr
      ⟨y, hbound y x hreach, hy⟩

abbrev PropEvidence (N : Type uN) := CPOG.DynamicSafety.PropEvidence N

def FDEIter (E : N → N → Prop) (σ : PropEvidence N) : Nat → PropEvidence N
  | 0 => σ
  | k + 1 => CPOG.DynamicSafety.FDEStep E (FDEIter E σ k)

theorem fdeIter_positive_iff_reachWithin
    (E : N → N → Prop) (σ : PropEvidence N) :
    ∀ k x, (FDEIter E σ k x).1 ↔
      ∃ y, ReachWithin E k y x ∧ (σ y).1 := by
  intro k
  induction k with
  | zero =>
      intro x
      constructor
      · intro hx
        exact ⟨x, rfl, hx⟩
      · rintro ⟨y, hyx, hy⟩
        subst y
        exact hy
  | succ k ih =>
      intro x
      change CPOG.DynamicSafety.SupportStep E
          (fun y => (FDEIter E σ k y).1) x ↔ _
      constructor
      · intro hx
        rcases hx with hx | ⟨z, hzx, hz⟩
        · rcases (ih x).mp hx with ⟨y, hyx, hy⟩
          exact ⟨y, Or.inl hyx, hy⟩
        · rcases (ih z).mp hz with ⟨y, hyz, hy⟩
          exact ⟨y, Or.inr ⟨z, hzx, hyz⟩, hy⟩
      · rintro ⟨y, hyx, hy⟩
        rcases hyx with hyx | ⟨z, hzx, hyz⟩
        · left
          exact (ih x).mpr ⟨y, hyx, hy⟩
        · right
          exact ⟨z, hzx, (ih z).mpr ⟨y, hyz, hy⟩⟩

theorem fdeIter_negative_iff_reachWithin
    (E : N → N → Prop) (σ : PropEvidence N) :
    ∀ k x, (FDEIter E σ k x).2 ↔
      ∃ y, ReachWithin E k y x ∧ (σ y).2 := by
  intro k
  induction k with
  | zero =>
      intro x
      constructor
      · intro hx
        exact ⟨x, rfl, hx⟩
      · rintro ⟨y, hyx, hy⟩
        subst y
        exact hy
  | succ k ih =>
      intro x
      change CPOG.DynamicSafety.SupportStep E
          (fun y => (FDEIter E σ k y).2) x ↔ _
      constructor
      · intro hx
        rcases hx with hx | ⟨z, hzx, hz⟩
        · rcases (ih x).mp hx with ⟨y, hyx, hy⟩
          exact ⟨y, Or.inl hyx, hy⟩
        · rcases (ih z).mp hz with ⟨y, hyz, hy⟩
          exact ⟨y, Or.inr ⟨z, hzx, hyz⟩, hy⟩
      · rintro ⟨y, hyx, hy⟩
        rcases hyx with hyx | ⟨z, hzx, hyz⟩
        · left
          exact (ih x).mpr ⟨y, hyx, hy⟩
        · right
          exact ⟨z, hzx, (ih z).mpr ⟨y, hyz, hy⟩⟩

theorem fdeIter_fixed_of_reachBound
    (E : N → N → Prop) (σ : PropEvidence N) (K : Nat)
    (hbound : ReachBoundedBy E K) :
    FDEIter E σ K = FDEIter E σ (K + 1) := by
  funext x
  apply Prod.ext
  · apply propext
    constructor
    · intro hx
      rcases (fdeIter_positive_iff_reachWithin E σ K x).mp hx with ⟨y, hyx, hy⟩
      exact (fdeIter_positive_iff_reachWithin E σ (K + 1) x).mpr
        ⟨y, reachWithin_mono E hyx, hy⟩
    · intro hx
      rcases (fdeIter_positive_iff_reachWithin E σ (K + 1) x).mp hx with ⟨y, hyx, hy⟩
      exact (fdeIter_positive_iff_reachWithin E σ K x).mpr
        ⟨y, hbound y x ⟨K + 1, hyx⟩, hy⟩
  · apply propext
    constructor
    · intro hx
      rcases (fdeIter_negative_iff_reachWithin E σ K x).mp hx with ⟨y, hyx, hy⟩
      exact (fdeIter_negative_iff_reachWithin E σ (K + 1) x).mpr
        ⟨y, reachWithin_mono E hyx, hy⟩
    · intro hx
      rcases (fdeIter_negative_iff_reachWithin E σ (K + 1) x).mp hx with ⟨y, hyx, hy⟩
      exact (fdeIter_negative_iff_reachWithin E σ K x).mpr
        ⟨y, hbound y x ⟨K + 1, hyx⟩, hy⟩


end CPOG.Convergence



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

/-- Equality at one round persists at every later adjacent round. -/
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
      simpa [Nat.add_assoc] using hnext

/-- If the process is fixed at k, then the k-th set equals every later k+d set. -/
theorem reachSet_eq_add_of_fixed [Fintype N]
    (E : N → N → Prop) (y : N) {k : Nat}
    (h : reachSet E y k = reachSet E y (k + 1)) :
    ∀ d, reachSet E y k = reachSet E y (k + d) := by
  intro d
  induction d with
  | zero => simp
  | succ d ih =>
      calc
        reachSet E y k = reachSet E y (k + d) := ih
        _ = reachSet E y (k + d + 1) := reachSet_eq_next_persists E y h d
        _ = reachSet E y (k + (d + 1)) := by
          rw [Nat.add_assoc]

/-- Reachability is monotone in the allowed path length. -/
theorem reachWithin_mono_le
    (E : N → N → Prop) {k m : Nat} {y x : N}
    (hkm : k ≤ m) (h : ReachWithin E k y x) :
    ReachWithin E m y x := by
  obtain ⟨d, hd⟩ := Nat.exists_eq_add_of_le hkm
  subst m
  clear hkm
  induction d with
  | zero =>
      simpa using h
  | succ d ih =>
      have hs := reachWithin_mono E ih
      simpa [Nat.add_assoc] using hs

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
    rw [mem_reachSet_iff]
    simp only [ReachWithin, Finset.mem_singleton]
    exact eq_comm
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
    have hk_le : k ≤ n - 1 := Nat.le_sub_one_of_lt hk
    obtain ⟨d, hd⟩ := Nat.exists_eq_add_of_le hk_le
    have hpersist := reachSet_eq_next_persists E y heq d
    have hfinal : reachSet E y (n - 1) = reachSet E y n := by
      calc
        reachSet E y (n - 1) = reachSet E y (k + d) := by rw [hd]
        _ = reachSet E y (k + d + 1) := hpersist
        _ = reachSet E y n := by
          have hone : 1 ≤ n := Nat.one_le_iff_ne_zero.mpr (Nat.ne_of_gt hnpos)
          have hnstep : n - 1 + 1 = n := Nat.sub_add_cancel hone
          rw [← hd, hnstep]
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
  have hpos : 0 < Fintype.card N := Fintype.card_pos_iff.mpr inferInstance
  have hKsucc : K + 1 = Fintype.card N := by
    dsimp [K]
    have hone : 1 ≤ Fintype.card N :=
      Nat.one_le_iff_ne_zero.mpr (Nat.ne_of_gt hpos)
    exact Nat.sub_add_cancel hone
  have hfix : reachSet E y K = reachSet E y (K + 1) := by
    rw [hKsucc]
    exact reachSet_fixed_card_sub_one E y
  by_cases hle : k ≤ K
  · exact reachWithin_mono_le E hle hk
  · have hKk : K ≤ k := Nat.le_of_lt (Nat.lt_of_not_ge hle)
    obtain ⟨d, hd⟩ := Nat.exists_eq_add_of_le hKk
    have heq := reachSet_eq_add_of_fixed E y hfix d
    have hxmem : x ∈ reachSet E y k :=
      (mem_reachSet_iff E y x k).2 hk
    have hxK : x ∈ reachSet E y K := by
      rw [heq, ← hd]
      exact hxmem
    exact (mem_reachSet_iff E y x K).1 hxK

/-- Sharp finite convergence bound for one-bit support propagation. -/
theorem supportIter_fixed_card_sub_one
    [Fintype N] [Nonempty N]
    (E : N → N → Prop) (S : N → Prop) :
    SupportIter E S (Fintype.card N - 1) =
      SupportIter E S (Fintype.card N) := by
  let K := Fintype.card N - 1
  have hbound : ReachBoundedBy E K := by
    simpa [K] using reachBoundedBy_card_sub_one E
  have h := supportIter_fixed_of_reachBound E S K hbound
  have hpos : 0 < Fintype.card N := Fintype.card_pos_iff.mpr inferInstance
  have hKsucc : K + 1 = Fintype.card N := by
    dsimp [K]
    have hone : 1 ≤ Fintype.card N :=
      Nat.one_le_iff_ne_zero.mpr (Nat.ne_of_gt hpos)
    exact Nat.sub_add_cancel hone
  rw [hKsucc] at h
  simpa [K] using h

/-- Sharp finite convergence bound for two-bit FDE propagation. -/
theorem fdeIter_fixed_card_sub_one
    [Fintype N] [Nonempty N]
    (E : N → N → Prop) (σ : PropEvidence N) :
    FDEIter E σ (Fintype.card N - 1) =
      FDEIter E σ (Fintype.card N) := by
  let K := Fintype.card N - 1
  have hbound : ReachBoundedBy E K := by
    simpa [K] using reachBoundedBy_card_sub_one E
  have h := fdeIter_fixed_of_reachBound E σ K hbound
  have hpos : 0 < Fintype.card N := Fintype.card_pos_iff.mpr inferInstance
  have hKsucc : K + 1 = Fintype.card N := by
    dsimp [K]
    have hone : 1 ≤ Fintype.card N :=
      Nat.one_le_iff_ne_zero.mpr (Nat.ne_of_gt hpos)
    exact Nat.sub_add_cancel hone
  rw [hKsucc] at h
  simpa [K] using h

end CPOG.FiniteConvergence
