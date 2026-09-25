import CPOG.General

/-!
Typed separation between monotone FDE evidence accumulation and decision-state
progress.  The paper uses these as different orders: G may extend evidence while
leaving the raw decision record fixed; D may change a decision record while
leaving the append-only evidence base fixed.
-/

namespace CPOG.DecisionSeparation

open CPOG.EpistemicPotentialism

/-- Componentwise information order on the FDE support pair. -/
def EvidenceLE (a b : Evidence) : Prop :=
  (a.pos = true → b.pos = true) ∧
  (a.neg = true → b.neg = true)

theorem evidenceLE_refl (a : Evidence) : EvidenceLE a a := by
  exact ⟨fun h => h, fun h => h⟩

theorem evidenceLE_trans {a b c : Evidence}
    (hab : EvidenceLE a b) (hbc : EvidenceLE b c) :
    EvidenceLE a c := by
  constructor
  · intro ha
    exact hbc.1 (hab.1 ha)
  · intro ha
    exact hbc.2 (hab.2 ha)

/-- FDE join only adds support in the information order. -/
theorem evidenceLE_join_left (a b : Evidence) :
    EvidenceLE a (joinEvidence a b) := by
  constructor
  · intro h
    simp [joinEvidence, h]
  · intro h
    simp [joinEvidence, h]

theorem evidenceLE_join_right (a b : Evidence) :
    EvidenceLE b (joinEvidence a b) := by
  constructor
  · intro h
    simp [joinEvidence, h]
  · intro h
    simp [joinEvidence, h]

/-- Abstract protocol-level progress on the separate decision-state type. -/
inductive DecisionStep : DecisionRecord → DecisionRecord → Prop where
  | openToContested : DecisionStep .openState .contested
  | openToPositive : DecisionStep .openState .resolvedPos
  | openToNegative : DecisionStep .openState .resolvedNeg
  | contestedToPositive : DecisionStep .contested .resolvedPos
  | contestedToNegative : DecisionStep .contested .resolvedNeg

/-- Combined state used only to state the orthogonality theorem explicitly. -/
structure EpistemicState where
  evidence : Evidence
  decision : DecisionRecord
  deriving DecidableEq, Repr

/-- A G-style evidence step preserves the raw decision record and grows evidence. -/
def GEvidenceStep (x y : EpistemicState) : Prop :=
  x.decision = y.decision ∧ EvidenceLE x.evidence y.evidence

/-- A D-style decision step preserves the evidence base and advances the decision record. -/
def DDecisionStep (x y : EpistemicState) : Prop :=
  x.evidence = y.evidence ∧ DecisionStep x.decision y.decision

theorem G_step_preserves_raw_decision {x y : EpistemicState}
    (h : GEvidenceStep x y) :
    x.decision = y.decision :=
  h.1

theorem G_step_is_information_inflationary {x y : EpistemicState}
    (h : GEvidenceStep x y) :
    EvidenceLE x.evidence y.evidence :=
  h.2

theorem D_step_preserves_evidence {x y : EpistemicState}
    (h : DDecisionStep x y) :
    x.evidence = y.evidence :=
  h.1

theorem D_step_is_not_defined_as_evidence_growth {x y : EpistemicState}
    (h : DDecisionStep x y) :
    EvidenceLE x.evidence y.evidence := by
  rw [h.1]
  exact evidenceLE_refl y.evidence

/--
The two progress notions are orthogonal by construction: G-growth is measured
in the FDE information order while D-progress is measured by DecisionStep.
-/
theorem evidence_and_decision_progress_are_typed_separately :
    (∀ x y, GEvidenceStep x y →
      EvidenceLE x.evidence y.evidence ∧ x.decision = y.decision) ∧
    (∀ x y, DDecisionStep x y →
      x.evidence = y.evidence ∧ DecisionStep x.decision y.decision) := by
  constructor
  · intro x y h
    exact ⟨h.2, h.1⟩
  · intro x y h
    exact h

/--
Concrete interaction law used by the paper: adding explicit negative support
is information-increasing, keeps the raw positive decision record available as
a record, yet makes that record effectively contested.
-/
theorem negative_evidence_reopens_without_mutating_raw_record (ev : Evidence) :
    EvidenceLE ev (joinEvidence ev evF) ∧
    effectiveDecision (joinEvidence ev evF) .resolvedPos = .contested := by
  exact ⟨evidenceLE_join_left ev evF,
    positive_resolution_reopens_after_negative_join ev⟩

end CPOG.DecisionSeparation
