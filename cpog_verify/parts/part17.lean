namespace CPOG

/-!
# v54 order-parametric Subsumption representation

The v51 theorem used the specific four-valued information order `InfoLe`.
Its proof only needs an order with reflexivity/transitivity plus monotonic
G-growth.  This section makes the order a parameter and recovers the InfoLe
result as a special case.  It also separates unrestricted information growth
from growth that does not newly introduce contradictory evidence.
-/

universe u

structure EvidencePreorder where
  rel : Rel Evidence
  refl : Reflexive rel
  trans : Transitive rel

structure OrderedEvidenceDynamics (O : EvidencePreorder) (W : Type u) where
  gR : Rel W
  dR : Rel W
  evidence : W -> Evidence
  decision : W -> DecisionState
  g_evidence_mono :
    forall {x y}, gR x y -> O.rel (evidence x) (evidence y)
  g_decision_same :
    forall {x y}, gR x y -> decision x = decision y
  d_reflexive : Reflexive dR

def OrderedEvidenceDynamics.PosOnly
    {W : Type u} {O : EvidencePreorder}
    (V : ViewFn) (S : OrderedEvidenceDynamics O W) (w : W) : Prop :=
  V (S.evidence w) (S.decision w) = .T

def PositiveRegionUpperClosedBy
    (O : EvidencePreorder) (V : ViewFn) : Prop :=
  forall (d : DecisionState) {e e' : Evidence},
    O.rel e e' ->
    V e d = .T ->
    V e' d = .T

def UniversalContentSubsumptionBy
    (O : EvidencePreorder) (V : ViewFn) : Prop :=
  forall {W : Type} (S : OrderedEvidenceDynamics O W) (w : W),
    Box S.dR (S.PosOnly V) w ->
    Box S.gR (S.PosOnly V) w

theorem upperClosedBy_implies_universalSubsumptionBy
    (O : EvidencePreorder) (V : ViewFn)
    (hUpper : PositiveRegionUpperClosedBy O V) :
    UniversalContentSubsumptionBy O V := by
  intro W S w hD y hwy
  have hAtW : S.PosOnly V w :=
    hD w (S.d_reflexive w)
  have hMono : O.rel (S.evidence w) (S.evidence y) :=
    S.g_evidence_mono hwy
  have hStable :
      V (S.evidence y) (S.decision w) = .T :=
    hUpper (S.decision w) hMono hAtW
  have hDec : S.decision w = S.decision y :=
    S.g_decision_same hwy
  simpa [OrderedEvidenceDynamics.PosOnly, hDec] using hStable

def orderedEvidencePairSystem
    (O : EvidencePreorder)
    (e e' : Evidence) (d : DecisionState)
    (hLe : O.rel e e') :
    OrderedEvidenceDynamics O EvidencePairWorld where
  gR := evidencePairG
  dR := evidencePairD
  evidence
    | .lower => e
    | .upper => e'
  decision := fun _ => d
  g_evidence_mono := by
    intro x y hxy
    cases x <;> cases y <;> simp [evidencePairG] at hxy
    · exact O.refl e
    · exact hLe
    · exact O.refl e'
  g_decision_same := by
    intro x y hxy
    rfl
  d_reflexive := by
    intro x
    rfl

theorem universalSubsumptionBy_implies_upperClosedBy
    (O : EvidencePreorder) (V : ViewFn)
    (hSub : UniversalContentSubsumptionBy O V) :
    PositiveRegionUpperClosedBy O V := by
  intro d e e' hLe hPos
  let S := orderedEvidencePairSystem O e e' d hLe
  have hD : Box S.dR (S.PosOnly V) .lower := by
    intro y hly
    have hy : EvidencePairWorld.lower = y := by
      simpa [S, orderedEvidencePairSystem, evidencePairD] using hly
    subst y
    exact hPos
  have hG : Box S.gR (S.PosOnly V) .lower :=
    hSub S .lower hD
  exact hG .upper (by trivial)

theorem order_parametric_subsumption_representation
    (O : EvidencePreorder) (V : ViewFn) :
    UniversalContentSubsumptionBy O V <->
      PositiveRegionUpperClosedBy O V := by
  constructor
  · exact universalSubsumptionBy_implies_upperClosedBy O V
  · exact upperClosedBy_implies_universalSubsumptionBy O V

def EvidenceDefeasibleBy
    (O : EvidencePreorder) (V : ViewFn) : Prop :=
  Not (PositiveRegionUpperClosedBy O V)

theorem order_parametric_subsumption_failure_iff_defeasible
    (O : EvidencePreorder) (V : ViewFn) :
    Not (UniversalContentSubsumptionBy O V) <->
      EvidenceDefeasibleBy O V := by
  unfold EvidenceDefeasibleBy
  exact not_congr (order_parametric_subsumption_representation O V)

theorem infoLe_trans
    {a b c : Evidence}
    (hab : InfoLe a b) (hbc : InfoLe b c) :
    InfoLe a c := by
  exact ⟨fun hp => hbc.1 (hab.1 hp),
    fun hn => hbc.2 (hab.2 hn)⟩

def infoEvidencePreorder : EvidencePreorder where
  rel := InfoLe
  refl := infoLe_refl
  trans := by
    intro a b c hab hbc
    exact infoLe_trans hab hbc

def NoContradictionGrowth (e e' : Evidence) : Prop :=
  InfoLe e e' /\ (e ≠ .B -> e' ≠ .B)

theorem noContradictionGrowth_refl :
    Reflexive NoContradictionGrowth := by
  intro e
  exact ⟨infoLe_refl e, fun h => h⟩

theorem noContradictionGrowth_trans :
    Transitive NoContradictionGrowth := by
  intro a b c hab hbc
  constructor
  · exact infoLe_trans hab.1 hbc.1
  · intro ha
    exact hbc.2 (hab.2 ha)

def noContradictionEvidencePreorder : EvidencePreorder where
  rel := NoContradictionGrowth
  refl := noContradictionGrowth_refl
  trans := noContradictionGrowth_trans

def identityView : ViewFn :=
  fun e _ => e

theorem identityView_not_upperClosed_fullInfo :
    Not (PositiveRegionUpperClosedBy infoEvidencePreorder identityView) := by
  intro hUpper
  have hB :
      identityView .B .resolvedPos = .T :=
    hUpper .resolvedPos infoLe_T_B rfl
  simp [identityView] at hB

theorem identityView_upperClosed_noContradiction :
    PositiveRegionUpperClosedBy noContradictionEvidencePreorder identityView := by
  intro d e e' hLe hPos
  simp [identityView] at hPos ⊢
  subst e
  cases e' <;>
    simp [noContradictionEvidencePreorder, NoContradictionGrowth,
      InfoLe, hasPos, hasNeg] at hLe ⊢

theorem identityView_subsumption_contrast :
    UniversalContentSubsumptionBy
        noContradictionEvidencePreorder identityView /\
    Not (UniversalContentSubsumptionBy
        infoEvidencePreorder identityView) := by
  constructor
  · exact
      (order_parametric_subsumption_representation
        noContradictionEvidencePreorder identityView).2
      identityView_upperClosed_noContradiction
  · intro hSub
    have hUpper :=
      (order_parametric_subsumption_representation
        infoEvidencePreorder identityView).1 hSub
    exact identityView_not_upperClosed_fullInfo hUpper

theorem fullInfo_subsumption_requires_B_positive
    (V : ViewFn) (d : DecisionState)
    (hSub : UniversalContentSubsumptionBy infoEvidencePreorder V)
    (hT : V .T d = .T) :
    V .B d = .T := by
  have hUpper :=
    (order_parametric_subsumption_representation
      infoEvidencePreorder V).1 hSub
  exact hUpper d infoLe_T_B hT

namespace SubmissionCoreV54

/--
SC5*. Order-parametric representation theorem.
For any explicit preorder of evidential growth, universal content Subsumption
over all monotone, decision-preserving systems holds exactly when the positive
region of V is upward closed in that preorder.
-/
theorem orderParametricSubsumptionIffUpperClosed
    (O : EvidencePreorder) (V : ViewFn) :
    UniversalContentSubsumptionBy O V <->
      PositiveRegionUpperClosedBy O V :=
  order_parametric_subsumption_representation O V

/-- SC6*. The corresponding failure theorem. -/
theorem orderParametricSubsumptionFailureIffDefeasible
    (O : EvidencePreorder) (V : ViewFn) :
    Not (UniversalContentSubsumptionBy O V) <->
      EvidenceDefeasibleBy O V :=
  order_parametric_subsumption_failure_iff_defeasible O V

/--
Full information growth makes contradiction-tolerance necessary:
if T is positive and universal Subsumption is required, B must remain positive.
-/
theorem fullInformationRequiresContradictionTolerance
    (V : ViewFn) (d : DecisionState)
    (hSub : UniversalContentSubsumptionBy infoEvidencePreorder V)
    (hT : V .T d = .T) :
    V .B d = .T :=
  fullInfo_subsumption_requires_B_positive V d hSub hT

/--
For the identity evaluator, Subsumption holds when growth cannot newly
introduce B, but fails for unrestricted information growth.
-/
theorem identityEvaluatorOrderContrast :
    UniversalContentSubsumptionBy
        noContradictionEvidencePreorder identityView /\
    Not (UniversalContentSubsumptionBy
        infoEvidencePreorder identityView) :=
  identityView_subsumption_contrast

end SubmissionCoreV54
end CPOG
