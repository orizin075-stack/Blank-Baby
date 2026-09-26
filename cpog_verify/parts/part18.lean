namespace CPOG

/-!
# Explicit recovery of the v51 InfoLe theorem

This adapter closes the presentation gap between the legacy EvidenceDynamics
structure and the v54 order-parametric OrderedEvidenceDynamics structure.
-/

universe u

def EvidenceDynamics.toInfoOrdered
    {W : Type u} (S : EvidenceDynamics W) :
    OrderedEvidenceDynamics infoEvidencePreorder W where
  gR := S.gR
  dR := S.dR
  evidence := S.evidence
  decision := S.decision
  g_evidence_mono := by
    intro x y hxy
    exact S.g_evidence_mono hxy
  g_decision_same := by
    intro x y hxy
    exact S.g_decision_same hxy
  d_reflexive := S.d_reflexive

def OrderedEvidenceDynamics.toLegacyInfo
    {W : Type u}
    (S : OrderedEvidenceDynamics infoEvidencePreorder W) :
    EvidenceDynamics W where
  gR := S.gR
  dR := S.dR
  evidence := S.evidence
  decision := S.decision
  g_evidence_mono := by
    intro x y hxy
    exact S.g_evidence_mono hxy
  g_decision_same := by
    intro x y hxy
    exact S.g_decision_same hxy
  d_reflexive := S.d_reflexive

theorem infoOrdered_subsumption_iff_legacy
    (V : ViewFn) :
    UniversalContentSubsumptionBy infoEvidencePreorder V <->
      UniversalContentSubsumption V := by
  constructor
  · intro hNew W S w hD
    let S' := S.toInfoOrdered
    have hD' : Box S'.dR (S'.PosOnly V) w := by
      simpa [S', EvidenceDynamics.toInfoOrdered,
        OrderedEvidenceDynamics.PosOnly, EvidenceDynamics.PosOnly] using hD
    have hG' : Box S'.gR (S'.PosOnly V) w :=
      hNew S' w hD'
    simpa [S', EvidenceDynamics.toInfoOrdered,
      OrderedEvidenceDynamics.PosOnly, EvidenceDynamics.PosOnly] using hG'
  · intro hOld W S w hD
    let S' := S.toLegacyInfo
    have hD' : Box S'.dR (S'.PosOnly V) w := by
      simpa [S', OrderedEvidenceDynamics.toLegacyInfo,
        OrderedEvidenceDynamics.PosOnly, EvidenceDynamics.PosOnly] using hD
    have hG' : Box S'.gR (S'.PosOnly V) w :=
      hOld S' w hD'
    simpa [S', OrderedEvidenceDynamics.toLegacyInfo,
      OrderedEvidenceDynamics.PosOnly, EvidenceDynamics.PosOnly] using hG'

theorem infoOrdered_upperClosed_iff_legacy
    (V : ViewFn) :
    PositiveRegionUpperClosedBy infoEvidencePreorder V <->
      PositiveRegionUpperClosed V := by
  rfl

theorem v51_InfoLe_representation_is_v54_instance
    (V : ViewFn) :
    UniversalContentSubsumption V <->
      PositiveRegionUpperClosed V := by
  rw [← infoOrdered_subsumption_iff_legacy V,
      ← infoOrdered_upperClosed_iff_legacy V]
  exact order_parametric_subsumption_representation
    infoEvidencePreorder V

end CPOG
