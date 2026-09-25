import CPOG.Possibility

namespace CPOG.MetaphysicalBridge

universe uW uF uT

variable {W : Type uW} {F : Type uF} {T : Type uT}

/-- External metaphysical possibility, deliberately outside the historical token semantics. -/
def PossMet (R : W → W → Prop) (Sat : W → F → Prop) (w : W) (φ : F) : Prop :=
  ∃ v, R w v ∧ Sat v φ

/-- Independent certification soundness for token content. -/
def CertificationSound
    (R : W → W → Prop) (Sat : W → F → Prop)
    (content : T → F) (Cert : W → T → W → Prop) : Prop :=
  ∀ ⦃w t v⦄, Cert w t v → R w v ∧ Sat v (content t)

/--
A historical/live token does not by itself imply metaphysical possibility; but an independent
sound certification witness does.
-/
theorem certification_implies_metaphysical_possibility
    (R : W → W → Prop) (Sat : W → F → Prop)
    (content : T → F) (Cert : W → T → W → Prop)
    (hsound : CertificationSound R Sat content Cert)
    {w : W} {t : T} {v : W}
    (hcert : Cert w t v) :
    PossMet R Sat w (content t) := by
  exact ⟨v, (hsound hcert).1, (hsound hcert).2⟩

end CPOG.MetaphysicalBridge
