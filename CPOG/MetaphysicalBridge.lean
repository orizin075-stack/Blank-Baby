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


/-! ## Independence witness: live epistemic possibility need not be metaphysically possible -/

def liveWitnessSystem :
    CPOG.Possibility.TokenSystem Unit Unit Unit Unit Unit where
  origin := fun _ => ()
  committedAt := fun _ _ => True
  liveAdmissible := fun _ _ _ _ => True
  futureAllowed := fun _ _ _ _ => True
  closed := fun _ _ _ _ => False

def noMetRel : Unit -> Unit -> Prop := fun _ _ => False

def noMetSat : Unit -> Unit -> Prop := fun _ _ => False

theorem live_without_metaphysical_possibility :
    CPOG.Possibility.PossLive liveWitnessSystem () () () () /\
    Not (PossMet noMetRel noMetSat () ()) := by
  constructor
  · exact ⟨True.intro, True.intro⟩
  · rintro ⟨v, hR, hSat⟩
    exact hR


/-- Historical generation by itself also does not imply metaphysical possibility. -/
theorem historical_without_metaphysical_possibility :
    CPOG.Possibility.PossHist liveWitnessSystem () () /\
    Not (PossMet noMetRel noMetSat () ()) := by
  constructor
  · exact CPOG.Possibility.possLive_implies_hist
      liveWitnessSystem
      (live_without_metaphysical_possibility).1
  · exact (live_without_metaphysical_possibility).2

end CPOG.MetaphysicalBridge
