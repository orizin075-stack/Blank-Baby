import CPOG.Dynamics
import Mathlib.Data.Fintype.Card
import Mathlib.Data.Finset.Card
import Mathlib.Tactic

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
