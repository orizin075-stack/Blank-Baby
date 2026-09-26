namespace CPOG

/-!
# Awareness/evidence interface

The class theorem in part13 constrains what happens when evidence changes
monotonically.  This tiny bridge lemma makes explicit the complementary point:
for a fixed tracked object, if an awareness-growth step leaves both its evidence
coordinate and its decision coordinate unchanged, then every extensional view
function preserves that object's positive judgement.  Any information carried
by awareness growth about an old object must therefore enter the model through
a changed evidence and/or decision coordinate (or through a changed semantic
identification before this theorem is applied).
-/

def TrackedCoordinatesUnchanged
    {W : Type u}
    (S : EvidenceDynamics W) (x y : W) : Prop :=
  S.evidence x = S.evidence y /\
  S.decision x = S.decision y

theorem unchanged_coordinates_preserve_PosOnly
    {W : Type u}
    (V : ViewFn) (S : EvidenceDynamics W)
    {x y : W}
    (h : TrackedCoordinatesUnchanged S x y) :
    S.PosOnly V x <-> S.PosOnly V y := by
  unfold TrackedCoordinatesUnchanged at h
  unfold EvidenceDynamics.PosOnly
  rw [h.1, h.2]

theorem pure_awareness_growth_is_judgment_silent
    {W : Type u}
    (V : ViewFn) (S : EvidenceDynamics W)
    {x y : W}
    (_hG : S.gR x y)
    (hE : S.evidence x = S.evidence y)
    (hD : S.decision x = S.decision y) :
    S.PosOnly V x <-> S.PosOnly V y := by
  exact unchanged_coordinates_preserve_PosOnly V S ⟨hE, hD⟩

end CPOG
