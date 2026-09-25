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


/-! ## Finite sharp bound by support-cardinality rank -/

/-- Encode one support predicate as a finite set. -/
noncomputable def supportFinset [Fintype N] (S : N → Prop) : Finset N := by
  classical
  exact Finset.univ.filter S

@[simp] theorem mem_supportFinset [Fintype N] (S : N → Prop) (x : N) :
    x ∈ supportFinset S ↔ S x := by
  classical
  simp [supportFinset]

theorem supportFinset_injective [Fintype N] :
    Function.Injective (supportFinset (N := N)) := by
  classical
  intro S T h
  funext x
  apply propext
  have hx := congrArg (fun U : Finset N => x ∈ U) h
  simpa using hx

theorem supportStep_inflationary
    (E : N → N → Prop) (S : N → Prop) :
    ∀ x, S x → CPOG.DynamicSafety.SupportStep E S x := by
  intro x hx
  exact Or.inl hx

theorem supportFinset_step_subset [Fintype N]
    (E : N → N → Prop) (S : N → Prop) :
    supportFinset S ⊆ supportFinset (CPOG.DynamicSafety.SupportStep E S) := by
  classical
  intro x hx
  exact (mem_supportFinset _ _).2
    (supportStep_inflationary E S x ((mem_supportFinset _ _).1 hx))

theorem supportStep_strict_card_growth [Fintype N]
    (E : N → N → Prop) (S : N → Prop)
    (hne : CPOG.DynamicSafety.SupportStep E S ≠ S) :
    (supportFinset S).card <
      (supportFinset (CPOG.DynamicSafety.SupportStep E S)).card := by
  classical
  have hsub := supportFinset_step_subset E S
  have hneFin :
      supportFinset S ≠ supportFinset (CPOG.DynamicSafety.SupportStep E S) := by
    intro h
    apply hne
    exact supportFinset_injective h
  exact Finset.card_lt_card (ssubset_of_subset_of_ne hsub hneFin)

theorem supportIter_from_step
    (E : N → N → Prop) (S : N → Prop) :
    ∀ k,
      SupportIter E (CPOG.DynamicSafety.SupportStep E S) k =
        SupportIter E S (k + 1) := by
  intro k
  induction k with
  | zero => rfl
  | succ k ih =>
      simp only [SupportIter, Nat.succ_eq_add_one]
      rw [ih]

theorem supportIter_add
    (E : N → N → Prop) (S : N → Prop) :
    ∀ m n,
      SupportIter E S (m + n) =
        SupportIter E (SupportIter E S m) n := by
  intro m n
  induction n with
  | zero =>
      simp [SupportIter]
  | succ n ih =>
      simp only [Nat.add_succ, SupportIter]
      rw [ih]

theorem supportIter_of_fixed
    (E : N → N → Prop) (S : N → Prop)
    (hfix : CPOG.DynamicSafety.SupportStep E S = S) :
    ∀ k, SupportIter E S k = S := by
  intro k
  induction k with
  | zero => rfl
  | succ k ih =>
      simp only [SupportIter]
      rw [ih, hfix]

theorem fixed_iter_propagates
    (E : N → N → Prop) (S : N → Prop)
    {k m : Nat}
    (hfix :
      CPOG.DynamicSafety.SupportStep E (SupportIter E S k) =
        SupportIter E S k)
    (hkm : k ≤ m) :
    CPOG.DynamicSafety.SupportStep E (SupportIter E S m) =
      SupportIter E S m := by
  obtain ⟨d, rfl⟩ := Nat.exists_eq_add_of_le hkm
  rw [supportIter_add E S k d]
  rw [supportIter_of_fixed E (SupportIter E S k) hfix d]
  exact hfix

/--
Rank theorem: a support bit reaches a fixed point within the number of nodes that
do not initially carry that support.
-/
theorem exists_support_fixed_within_deficit [Fintype N]
    (E : N → N → Prop) (S : N → Prop) :
    ∃ k ≤ Fintype.card N - (supportFinset S).card,
      CPOG.DynamicSafety.SupportStep E (SupportIter E S k) =
        SupportIter E S k := by
  classical
  let cardN := Fintype.card N
  have aux :
      ∀ d : Nat, ∀ T : N → Prop,
        cardN - (supportFinset T).card = d →
        ∃ k ≤ d,
          CPOG.DynamicSafety.SupportStep E (SupportIter E T k) =
            SupportIter E T k := by
    intro d
    induction d using Nat.strong_induction_on with
    | h d ih =>
        intro T hd
        by_cases hfix : CPOG.DynamicSafety.SupportStep E T = T
        · exact ⟨0, Nat.zero_le d, by simpa [SupportIter] using hfix⟩
        · have hcard :
              (supportFinset T).card <
                (supportFinset (CPOG.DynamicSafety.SupportStep E T)).card :=
            supportStep_strict_card_growth E T hfix
          have hle :
              (supportFinset (CPOG.DynamicSafety.SupportStep E T)).card ≤ cardN := by
            exact Finset.card_le_univ _
          let d' := cardN -
            (supportFinset (CPOG.DynamicSafety.SupportStep E T)).card
          have hdlt : d' < d := by
            dsimp [d', cardN] at *
            omega
          obtain ⟨k, hk, hkfix⟩ :=
            ih d' hdlt (CPOG.DynamicSafety.SupportStep E T) rfl
          refine ⟨k + 1, ?_, ?_⟩
          · dsimp [d', cardN] at hk ⊢
            omega
          · rw [← supportIter_from_step E T k]
            exact hkfix
  exact aux (Fintype.card N - (supportFinset S).card) S rfl

theorem empty_support_fixed
    (E : N → N → Prop) :
    CPOG.DynamicSafety.SupportStep E (fun _ => False) =
      (fun _ => False) := by
  funext x
  apply propext
  constructor
  · intro h
    rcases h with h | ⟨y, _hE, hy⟩
    · exact h
    · exact hy
  · intro h
    exact False.elim h

/--
Sharp uniform finite bound for one support bit: on a nonempty finite node type,
the state at round |N|-1 is already a fixed point.
-/
theorem support_fixed_at_card_sub_one [Fintype N]
    (hN : 0 < Fintype.card N)
    (E : N → N → Prop) (S : N → Prop) :
    CPOG.DynamicSafety.SupportStep E
        (SupportIter E S (Fintype.card N - 1)) =
      SupportIter E S (Fintype.card N - 1) := by
  classical
  by_cases hS : (supportFinset S).Nonempty
  · obtain ⟨k, hk, hfix⟩ := exists_support_fixed_within_deficit E S
    have hcardPos : 0 < (supportFinset S).card := Finset.card_pos.mpr hS
    have hbound :
        Fintype.card N - (supportFinset S).card ≤ Fintype.card N - 1 := by
      omega
    exact fixed_iter_propagates E S hfix (hk.trans hbound)
  · have hEmpty : supportFinset S = ∅ :=
      Finset.not_nonempty_iff_eq_empty.mp hS
    have hFalse : S = (fun _ => False) := by
      apply supportFinset_injective
      rw [hEmpty]
      simp [supportFinset]
    subst S
    have hfix := empty_support_fixed (N := N) E
    exact fixed_iter_propagates E (fun _ => False) hfix (Nat.zero_le _)

/--
Sharp finite FDE convergence theorem. Positive and negative support propagate in
parallel, so the two-bit state stabilizes by |N|-1 rather than 2|N|.
-/
theorem FDE_fixed_at_card_sub_one [Fintype N]
    (hN : 0 < Fintype.card N)
    (E : N → N → Prop) (σ : PropEvidence N) :
    CPOG.DynamicSafety.FDEStep E
        (FDEIter E σ (Fintype.card N - 1)) =
      FDEIter E σ (Fintype.card N - 1) := by
  have hpos :=
    support_fixed_at_card_sub_one hN E (fun y => (σ y).1)
  have hneg :=
    support_fixed_at_card_sub_one hN E (fun y => (σ y).2)
  funext x
  apply Prod.ext
  · exact congrFun hpos x
  · exact congrFun hneg x

end CPOG.Convergence
