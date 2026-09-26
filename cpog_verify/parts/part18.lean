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

theorem legacy_posOnly_iff_infoOrdered
    {W : Type u} (V : ViewFn) (S : EvidenceDynamics W) (w : W) :
    S.PosOnly V w <-> S.toInfoOrdered.PosOnly V w := by
  rfl

theorem infoOrdered_posOnly_iff_legacy
    {W : Type u} (V : ViewFn)
    (S : OrderedEvidenceDynamics infoEvidencePreorder W) (w : W) :
    S.PosOnly V w <-> S.toLegacyInfo.PosOnly V w := by
  rfl

theorem infoOrdered_subsumption_iff_legacy
    (V : ViewFn) :
    UniversalContentSubsumptionBy infoEvidencePreorder V <->
      UniversalContentSubsumption V := by
  constructor
  · intro hNew W S w hD
    let S' := S.toInfoOrdered
    have hD' : Box S'.dR (S'.PosOnly V) w := by
      intro y hwy
      exact (legacy_posOnly_iff_infoOrdered V S y).mp (hD y hwy)
    have hG' : Box S'.gR (S'.PosOnly V) w :=
      hNew S' w hD'
    intro y hwy
    exact (legacy_posOnly_iff_infoOrdered V S y).mpr (hG' y hwy)
  · intro hOld W S w hD
    let S' := S.toLegacyInfo
    have hD' : Box S'.dR (S'.PosOnly V) w := by
      intro y hwy
      exact (infoOrdered_posOnly_iff_legacy V S y).mp (hD y hwy)
    have hG' : Box S'.gR (S'.PosOnly V) w :=
      hOld S' w hD'
    intro y hwy
    exact (infoOrdered_posOnly_iff_legacy V S y).mpr (hG' y hwy)

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
