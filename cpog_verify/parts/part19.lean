namespace CPOG

/-!
# v55 abstract update-growth representation theorem

The v54 theorem still fixed the semantic carrier to the four-valued Evidence
type and encoded the decision component separately.  The present theorem
abstracts over the whole evaluative input carrier X.

An admissible growth specification is just a reflexive relation on X.
Actual G-steps are required to respect that relation.  The accepted region may
be any predicate A : X -> Prop.  Universal Subsumption over every dynamics
respecting the admissible growth relation is equivalent to upward closure of A.

This strictly subsumes the v54 evidence-preorder theorem by taking
X := Evidence × DecisionState and
  ((e,d) <= (e',d')) :<=> P.le e e' /\ d = d'.
It also permits decision-changing growth by changing the relation on the second
coordinate rather than rebuilding the theorem.
-/

universe u v

structure GrowthSpec (X : Type u) where
  rel : Rel X
  refl : Reflexive rel

structure AbstractUpdateDynamics
    {X : Type u} (G : GrowthSpec X) (W : Type v) where
  gR : Rel W
  dR : Rel W
  input : W -> X
  g_respects :
    forall {x y : W}, gR x y -> G.rel (input x) (input y)
  d_reflexive : Reflexive dR

def AbstractUpdateDynamics.Accepted
    {X : Type u} {G : GrowthSpec X} {W : Type v}
    (A : X -> Prop) (S : AbstractUpdateDynamics G W) (w : W) : Prop :=
  A (S.input w)

def UpwardClosedOn
    {X : Type u} (G : GrowthSpec X) (A : X -> Prop) : Prop :=
  forall {x y : X}, G.rel x y -> A x -> A y

def UniversalSubsumptionOn
    {X : Type u} (G : GrowthSpec X) (A : X -> Prop) : Prop :=
  forall {W : Type} (S : AbstractUpdateDynamics G W) (w : W),
    Box S.dR (S.Accepted A) w ->
    Box S.gR (S.Accepted A) w

theorem abstract_upwardClosed_implies_universalSubsumption
    {X : Type u}
    (G : GrowthSpec X) (A : X -> Prop)
    (hUpper : UpwardClosedOn G A) :
    UniversalSubsumptionOn G A := by
  intro W S w hD y hwy
  have hAtW : S.Accepted A w :=
    hD w (S.d_reflexive w)
  exact hUpper (S.g_respects hwy) hAtW

inductive AbstractPairWorld where
  | lower
  | upper

deriving DecidableEq

def abstractPairG : Rel AbstractPairWorld
  | .lower, .lower => True
  | .lower, .upper => True
  | .upper, .upper => True
  | .upper, .lower => False

def abstractPairD : Rel AbstractPairWorld :=
  fun x y => x = y

def abstractPairSystem
    {X : Type u}
    (G : GrowthSpec X)
    (x y : X)
    (hxy : G.rel x y) :
    AbstractUpdateDynamics G AbstractPairWorld where
  gR := abstractPairG
  dR := abstractPairD
  input
    | .lower => x
    | .upper => y
  g_respects := by
    intro a b hab
    cases a <;> cases b <;> simp [abstractPairG] at hab
    · exact G.refl x
    · exact hxy
    · exact G.refl y
  d_reflexive := by
    intro z
    rfl

theorem abstract_universalSubsumption_implies_upwardClosed
    {X : Type u}
    (G : GrowthSpec X) (A : X -> Prop)
    (hSub : UniversalSubsumptionOn G A) :
    UpwardClosedOn G A := by
  intro x y hxy hAx
  let S := abstractPairSystem G x y hxy
  have hD : Box S.dR (S.Accepted A) AbstractPairWorld.lower := by
    intro z hlz
    have hz : AbstractPairWorld.lower = z := by
      simpa [S, abstractPairSystem, abstractPairD] using hlz
    subst z
    exact hAx
  have hG : Box S.gR (S.Accepted A) AbstractPairWorld.lower :=
    hSub S .lower hD
  exact hG AbstractPairWorld.upper (by trivial)

theorem abstract_universalSubsumption_iff_upwardClosed
    {X : Type u}
    (G : GrowthSpec X) (A : X -> Prop) :
    UniversalSubsumptionOn G A <-> UpwardClosedOn G A := by
  constructor
  · exact abstract_universalSubsumption_implies_upwardClosed G A
  · exact abstract_upwardClosed_implies_universalSubsumption G A

def AbstractDefeasible
    {X : Type u} (G : GrowthSpec X) (A : X -> Prop) : Prop :=
  Not (UpwardClosedOn G A)

theorem abstract_universalSubsumption_failure_iff_defeasible
    {X : Type u}
    (G : GrowthSpec X) (A : X -> Prop) :
    Not (UniversalSubsumptionOn G A) <->
      AbstractDefeasible G A := by
  unfold AbstractDefeasible
  exact not_congr (abstract_universalSubsumption_iff_upwardClosed G A)

/-! ## Exact recovery of the v54 evidence-preorder theorem -/

abbrev EvaluationInput := Evidence × DecisionState

def viewAccepted (V : ViewFn) : EvaluationInput -> Prop :=
  fun z => V z.1 z.2 = .T

def evidenceDecisionGrowth
    (P : EvidencePreorder) : GrowthSpec EvaluationInput where
  rel := fun x y => P.le x.1 y.1 /\ x.2 = y.2
  refl := by
    intro z
    exact ⟨P.refl z.1, rfl⟩

theorem positiveRegionUpperClosedBy_iff_abstract
    (P : EvidencePreorder) (V : ViewFn) :
    PositiveRegionUpperClosedBy P V <->
      UpwardClosedOn (evidenceDecisionGrowth P) (viewAccepted V) := by
  constructor
  · intro hUpper x y hxy hPos
    have hStable : V y.1 x.2 = .T :=
      hUpper x.2 hxy.1 hPos
    simpa [viewAccepted, hxy.2] using hStable
  · intro hUpper d e e' hLe hPos
    have hStable :=
      hUpper
        (x := (e, d))
        (y := (e', d))
        ⟨hLe, rfl⟩
        hPos
    exact hStable

theorem evidenceUniversalSubsumptionBy_iff_abstract
    (P : EvidencePreorder) (V : ViewFn) :
    UniversalContentSubsumptionBy P V <->
      UniversalSubsumptionOn
        (evidenceDecisionGrowth P)
        (viewAccepted V) := by
  constructor
  · intro hOld
    have hUpperOld : PositiveRegionUpperClosedBy P V :=
      (preorder_universal_subsumption_iff_upperClosed P V).mp hOld
    have hUpperAbstract :
        UpwardClosedOn
          (evidenceDecisionGrowth P)
          (viewAccepted V) :=
      (positiveRegionUpperClosedBy_iff_abstract P V).mp hUpperOld
    exact
      (abstract_universalSubsumption_iff_upwardClosed
        (evidenceDecisionGrowth P)
        (viewAccepted V)).mpr
        hUpperAbstract
  · intro hAbstract
    have hUpperAbstract :
        UpwardClosedOn
          (evidenceDecisionGrowth P)
          (viewAccepted V) :=
      (abstract_universalSubsumption_iff_upwardClosed
        (evidenceDecisionGrowth P)
        (viewAccepted V)).mp
        hAbstract
    have hUpperOld : PositiveRegionUpperClosedBy P V :=
      (positiveRegionUpperClosedBy_iff_abstract P V).mpr hUpperAbstract
    exact
      (preorder_universal_subsumption_iff_upperClosed P V).mpr
        hUpperOld

/-! ## Product growth: evidence and decision may both change -/

def productEvaluationGrowth
    (PE : EvidencePreorder)
    (PD : GrowthSpec DecisionState) :
    GrowthSpec EvaluationInput where
  rel := fun x y => PE.le x.1 y.1 /\ PD.rel x.2 y.2
  refl := by
    intro z
    exact ⟨PE.refl z.1, PD.refl z.2⟩

def UniversalEvaluationSubsumption
    (PE : EvidencePreorder)
    (PD : GrowthSpec DecisionState)
    (V : ViewFn) : Prop :=
  UniversalSubsumptionOn (productEvaluationGrowth PE PD) (viewAccepted V)

def EvaluationRegionUpperClosed
    (PE : EvidencePreorder)
    (PD : GrowthSpec DecisionState)
    (V : ViewFn) : Prop :=
  UpwardClosedOn (productEvaluationGrowth PE PD) (viewAccepted V)

theorem evaluation_subsumption_iff_product_upperClosed
    (PE : EvidencePreorder)
    (PD : GrowthSpec DecisionState)
    (V : ViewFn) :
    UniversalEvaluationSubsumption PE PD V <->
      EvaluationRegionUpperClosed PE PD V := by
  exact
    abstract_universalSubsumption_iff_upwardClosed
      (productEvaluationGrowth PE PD)
      (viewAccepted V)

/-!
The theorem above removes the v54 "decision-preserving" restriction.
A decision-changing G-step is admissible whenever its decision-coordinate change
lies in PD.rel.  Stability is then exactly upward closure in the product growth
relation.
-/

end CPOG
