namespace CPOG

/-!
# v55 generic state-growth representation theorem

The v54 theorem is still tied to the four-valued Evidence carrier and a
decision coordinate.  The proof itself needs neither.  This section isolates
the minimal structure:

* an arbitrary summary-state type S;
* an arbitrary admissible-growth relation on S;
* a G-transition system whose summary is monotone in that relation;
* a reflexive D-relation;
* an arbitrary acceptance predicate A : S -> Prop.

Universal G-over-D Subsumption is then equivalent to upward closure of A under
the chosen growth relation.  No lattice structure, four-valued semantics,
decision type, or transitivity assumption is required.
-/

universe u v

structure StateGrowth (S : Type u) where
  rel : Rel S

structure StatePreorder (S : Type u) extends StateGrowth S where
  refl : Reflexive rel
  trans : Transitive rel

structure GrowthDynamics
    {S : Type u} (G : StateGrowth S) (W : Type v) where
  gR : Rel W
  dR : Rel W
  summary : W -> S
  g_summary_mono :
    forall {x y}, gR x y -> G.rel (summary x) (summary y)
  d_reflexive : Reflexive dR

def GrowthDynamics.Accepts
    {S : Type u} {G : StateGrowth S} {W : Type v}
    (A : S -> Prop) (M : GrowthDynamics G W) (w : W) : Prop :=
  A (M.summary w)

def StateUpperClosed
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) : Prop :=
  forall {s s' : S}, G.rel s s' -> A s -> A s'

def StateDefeasible
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) : Prop :=
  Not (StateUpperClosed G A)

def UniversalStateSubsumption
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) : Prop :=
  forall {W : Type} (M : GrowthDynamics G W) (w : W),
    Box M.dR (M.Accepts A) w ->
    Box M.gR (M.Accepts A) w

theorem state_upperClosed_implies_universal_subsumption
    {S : Type u} (G : StateGrowth S) (A : S -> Prop)
    (hUpper : StateUpperClosed G A) :
    UniversalStateSubsumption G A := by
  intro W M w hD y hwy
  have hAtW : M.Accepts A w :=
    hD w (M.d_reflexive w)
  exact hUpper (M.g_summary_mono hwy) hAtW

inductive GenericPairWorld where
  | lower
  | upper

deriving DecidableEq

def genericPairG : Rel GenericPairWorld
  | .lower, .upper => True
  | _, _ => False

def genericPairD : Rel GenericPairWorld :=
  fun x y => x = y

def genericPairDynamics
    {S : Type u}
    (G : StateGrowth S)
    (s s' : S)
    (hss : G.rel s s') :
    GrowthDynamics G GenericPairWorld where
  gR := genericPairG
  dR := genericPairD
  summary
    | .lower => s
    | .upper => s'
  g_summary_mono := by
    intro x y hxy
    cases x <;> cases y <;> simp [genericPairG] at hxy
    exact hss
  d_reflexive := by
    intro x
    rfl

theorem universal_subsumption_implies_state_upperClosed
    {S : Type u} (G : StateGrowth S) (A : S -> Prop)
    (hSub : UniversalStateSubsumption G A) :
    StateUpperClosed G A := by
  intro s s' hss hA
  let M := genericPairDynamics G s s' hss
  have hD : Box M.dR (M.Accepts A) .lower := by
    intro y hly
    have hy : GenericPairWorld.lower = y := by
      simpa [M, genericPairDynamics, genericPairD] using hly
    subst y
    exact hA
  have hG : Box M.gR (M.Accepts A) .lower :=
    hSub M .lower hD
  exact hG .upper (by trivial)

/--
MASTER REPRESENTATION THEOREM.
For every admissible-growth relation on an arbitrary summary-state carrier
and every acceptance predicate, universal G-over-D Subsumption is equivalent
to upward closure of acceptance under admissible growth. No reflexivity or
transitivity of the growth relation is required.
-/
theorem universal_state_subsumption_iff_upperClosed
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    UniversalStateSubsumption G A <-> StateUpperClosed G A := by
  constructor
  · exact universal_subsumption_implies_state_upperClosed G A
  · exact state_upperClosed_implies_universal_subsumption G A

theorem universal_state_subsumption_failure_iff_defeasible
    {S : Type u} (G : StateGrowth S) (A : S -> Prop) :
    Not (UniversalStateSubsumption G A) <-> StateDefeasible G A := by
  unfold StateDefeasible
  exact not_congr (universal_state_subsumption_iff_upperClosed G A)

/-! ## v54 as an exact instance of the generic theorem -/

def evidenceDecisionGrowth
    (P : EvidencePreorder) :
    StateGrowth (Evidence × DecisionState) where
  rel := fun x y => P.le x.1 y.1 /\ x.2 = y.2

def acceptByView (V : ViewFn) :
    (Evidence × DecisionState) -> Prop :=
  fun z => V z.1 z.2 = .T

theorem positiveRegionUpperClosedBy_iff_stateUpperClosed
    (P : EvidencePreorder) (V : ViewFn) :
    PositiveRegionUpperClosedBy P V <->
      StateUpperClosed (evidenceDecisionGrowth P) (acceptByView V) := by
  constructor
  · intro h dstate dstate' hRel hPos
    simpa [acceptByView, hRel.2] using h (dstate.2) hRel.1 hPos
  · intro h d e e' hLe hPos
    have hRel :
        (evidenceDecisionGrowth P).rel (e, d) (e', d) :=
      ⟨hLe, rfl⟩
    exact h hRel hPos

theorem v54_representation_is_generic_state_instance
    (P : EvidencePreorder) (V : ViewFn) :
    UniversalContentSubsumptionBy P V <->
      StateUpperClosed (evidenceDecisionGrowth P) (acceptByView V) := by
  calc
    UniversalContentSubsumptionBy P V
        <-> PositiveRegionUpperClosedBy P V :=
      preorder_universal_subsumption_iff_upperClosed P V
    _ <-> StateUpperClosed (evidenceDecisionGrowth P) (acceptByView V) :=
      positiveRegionUpperClosedBy_iff_stateUpperClosed P V

theorem v54_subsumption_iff_generic_universal_subsumption
    (P : EvidencePreorder) (V : ViewFn) :
    UniversalContentSubsumptionBy P V <->
      UniversalStateSubsumption
        (evidenceDecisionGrowth P) (acceptByView V) := by
  rw [v54_representation_is_generic_state_instance]
  exact
    (universal_state_subsumption_iff_upperClosed
      (evidenceDecisionGrowth P) (acceptByView V)).symm

/-! ## Generic awareness-silence -/

theorem unchanged_summary_preserves_acceptance
    {S : Type u} (A : S -> Prop)
    {W : Type v} {G : StateGrowth S}
    (M : GrowthDynamics G W)
    {x y : W}
    (h : M.summary x = M.summary y) :
    M.Accepts A x <-> M.Accepts A y := by
  unfold GrowthDynamics.Accepts
  rw [h]

end CPOG
