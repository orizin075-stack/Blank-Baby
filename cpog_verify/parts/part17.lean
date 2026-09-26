namespace CPOG

/-!
# v54 order-parametric Subsumption

The v51 theorem used the four-valued information order `InfoLe`.
Its proof only needs an evidence-growth relation with reflexive self-growth.
This section packages an arbitrary preorder on Evidence and proves the same
representation theorem uniformly.  The original `InfoLe` theorem is one
instance; a no-new-negative-support preorder yields the contrasting stable case.
-/

structure EvidencePreorder where
  le : Rel Evidence
  refl : Reflexive le
  trans : Transitive le

structure PreorderEvidenceDynamics (P : EvidencePreorder) (W : Type u) where
  gR : Rel W
  dR : Rel W
  evidence : W -> Evidence
  decision : W -> DecisionState
  g_evidence_mono :
    forall {x y}, gR x y -> P.le (evidence x) (evidence y)
  g_decision_same :
    forall {x y}, gR x y -> decision x = decision y
  d_reflexive : Reflexive dR

def PreorderEvidenceDynamics.PosOnly
    {W : Type u} {P : EvidencePreorder}
    (V : ViewFn) (S : PreorderEvidenceDynamics P W) (w : W) : Prop :=
  V (S.evidence w) (S.decision w) = .T

def PositiveRegionUpperClosedBy
    (P : EvidencePreorder) (V : ViewFn) : Prop :=
  forall (d : DecisionState) {e e' : Evidence},
    P.le e e' ->
    V e d = .T ->
    V e' d = .T

def EvidenceDefeasibleBy
    (P : EvidencePreorder) (V : ViewFn) : Prop :=
  Not (PositiveRegionUpperClosedBy P V)

def UniversalContentSubsumptionBy
    (P : EvidencePreorder) (V : ViewFn) : Prop :=
  forall {W : Type} (S : PreorderEvidenceDynamics P W) (w : W),
    Box S.dR (S.PosOnly V) w ->
    Box S.gR (S.PosOnly V) w

theorem preorder_upperClosed_implies_universal_subsumption
    (P : EvidencePreorder) (V : ViewFn)
    (hUpper : PositiveRegionUpperClosedBy P V) :
    UniversalContentSubsumptionBy P V := by
  intro W S w hD y hwy
  have hAtW : S.PosOnly V w :=
    hD w (S.d_reflexive w)
  have hMono : P.le (S.evidence w) (S.evidence y) :=
    S.g_evidence_mono hwy
  have hStable :
      V (S.evidence y) (S.decision w) = .T :=
    hUpper (S.decision w) hMono hAtW
  have hDec : S.decision w = S.decision y :=
    S.g_decision_same hwy
  simpa [PreorderEvidenceDynamics.PosOnly, hDec] using hStable

def preorderEvidencePairSystem
    (P : EvidencePreorder)
    (e e' : Evidence) (d : DecisionState)
    (hLe : P.le e e') :
    PreorderEvidenceDynamics P EvidencePairWorld where
  gR := evidencePairG
  dR := evidencePairD
  evidence
    | .lower => e
    | .upper => e'
  decision := fun _ => d
  g_evidence_mono := by
    intro x y hxy
    cases x <;> cases y <;> simp [evidencePairG] at hxy
    · exact P.refl e
    · exact hLe
    · exact P.refl e'
  g_decision_same := by
    intro x y hxy
    rfl
  d_reflexive := by
    intro x
    rfl

theorem preorder_universal_subsumption_implies_upperClosed
    (P : EvidencePreorder) (V : ViewFn)
    (hSub : UniversalContentSubsumptionBy P V) :
    PositiveRegionUpperClosedBy P V := by
  intro d e e' hLe hPos
  let S := preorderEvidencePairSystem P e e' d hLe
  have hD : Box S.dR (S.PosOnly V) .lower := by
    intro y hly
    have hy : EvidencePairWorld.lower = y := by
      simpa [S, preorderEvidencePairSystem, evidencePairD] using hly
    subst y
    exact hPos
  have hG : Box S.gR (S.PosOnly V) .lower :=
    hSub S .lower hD
  exact hG .upper (by trivial)

theorem preorder_universal_subsumption_iff_upperClosed
    (P : EvidencePreorder) (V : ViewFn) :
    UniversalContentSubsumptionBy P V <->
      PositiveRegionUpperClosedBy P V := by
  constructor
  · exact preorder_universal_subsumption_implies_upperClosed P V
  · exact preorder_upperClosed_implies_universal_subsumption P V

theorem preorder_universal_subsumption_failure_iff_defeasible
    (P : EvidencePreorder) (V : ViewFn) :
    Not (UniversalContentSubsumptionBy P V) <->
      EvidenceDefeasibleBy P V := by
  unfold EvidenceDefeasibleBy
  exact not_congr (preorder_universal_subsumption_iff_upperClosed P V)

theorem infoLe_transitive : Transitive InfoLe := by
  intro a b c hab hbc
  constructor
  · intro hpa
    exact hbc.1 (hab.1 hpa)
  · intro hna
    exact hbc.2 (hab.2 hna)

def infoEvidencePreorder : EvidencePreorder where
  le := InfoLe
  refl := infoLe_refl
  trans := infoLe_transitive

def identityView : ViewFn := fun e _ => e

theorem info_upperClosed_T_forces_B
    (V : ViewFn)
    (hUpper : PositiveRegionUpperClosedBy infoEvidencePreorder V)
    (d : DecisionState)
    (hT : V .T d = .T) :
    V .B d = .T := by
  exact hUpper d infoLe_T_B hT

theorem info_universal_subsumption_T_forces_B
    (V : ViewFn)
    (hSub : UniversalContentSubsumptionBy infoEvidencePreorder V)
    (d : DecisionState)
    (hT : V .T d = .T) :
    V .B d = .T := by
  have hUpper :
      PositiveRegionUpperClosedBy infoEvidencePreorder V :=
    (preorder_universal_subsumption_iff_upperClosed
      infoEvidencePreorder V).mp hSub
  exact info_upperClosed_T_forces_B V hUpper d hT

theorem info_T_to_B_refutation_forces_subsumption_failure
    (V : ViewFn) (d : DecisionState)
    (hT : V .T d = .T) (hB : V .B d != .T) :
    Not (UniversalContentSubsumptionBy infoEvidencePreorder V) := by
  intro hSub
  exact hB (info_universal_subsumption_T_forces_B V hSub d hT)

theorem identityView_not_info_upperClosed :
    Not (PositiveRegionUpperClosedBy infoEvidencePreorder identityView) := by
  intro hUpper
  have hBT : identityView .B .resolvedPos = .T :=
    hUpper .resolvedPos infoLe_T_B rfl
  change Evidence.B = Evidence.T at hBT
  cases hBT

theorem identityView_fails_info_universal_subsumption :
    Not (UniversalContentSubsumptionBy infoEvidencePreorder identityView) := by
  exact
    (preorder_universal_subsumption_failure_iff_defeasible
      infoEvidencePreorder identityView).mpr
      identityView_not_info_upperClosed

def NoNewNegativeLe (a b : Evidence) : Prop :=
  InfoLe a b / (hasNeg b -> hasNeg a)

theorem noNewNegative_refl : Reflexive NoNewNegativeLe := by
  intro e
  exact ⟨infoLe_refl e, fun h => h⟩

theorem noNewNegative_trans : Transitive NoNewNegativeLe := by
  intro a b c hab hbc
  constructor
  · exact infoLe_transitive hab.1 hbc.1
  · intro hnc
    exact hab.2 (hbc.2 hnc)

def noNewNegativePreorder : EvidencePreorder where
  le := NoNewNegativeLe
  refl := noNewNegative_refl
  trans := noNewNegative_trans

theorem identityView_noNewNegative_upperClosed :
    PositiveRegionUpperClosedBy noNewNegativePreorder identityView := by
  intro d e e' hLe hPos
  change e = Evidence.T at hPos
  subst e
  change e' = Evidence.T
  rcases hLe with ⟨hInfo, hNoNewNeg⟩
  cases e' with
  | N =>
      exact False.elim (hInfo.1 (by trivial))
  | T =>
      rfl
  | F =>
      exact False.elim (hNoNewNeg (by trivial))
  | B =>
      exact False.elim (hNoNewNeg (by trivial))

theorem identityView_recovers_noNewNegative_subsumption :
    UniversalContentSubsumptionBy noNewNegativePreorder identityView := by
  exact
    (preorder_universal_subsumption_iff_upperClosed
      noNewNegativePreorder identityView).mpr
      identityView_noNewNegative_upperClosed

end CPOG
