import CPOG.Possibility

/-!
A deliberately weak bridge to Levi-style serious possibility.

This module does not identify CPOG live possibility with Levi's theory.  It
formalizes only the conditional claim made in the paper: under a compatibility
policy saying that every admitted live token has serious content, PossLive
implies Serious.  The converse is not derivable in general.
-/

namespace CPOG.LeviBridge

open CPOG.Possibility

universe uH uC uT uU uP uF

variable {H : Type uH} {C : Type uC} {T : Type uT}
variable {U : Type uU} {P : Type uP} {F : Type uF}

/--
Compatibility condition between a CPOG live-admission policy and an externally
specified serious-possibility predicate.
-/
def LeviCompatible
    (S : TokenSystem H C T U P)
    (content : T → F)
    (Serious : H → F → Prop) : Prop :=
  ∀ h u p t,
    S.liveAdmissible h u p t →
    Serious h (content t)

/--
Formal bridge used in the paper: with a Levi-compatible admission policy, every
live possibility has serious content.
-/
theorem possLive_implies_serious_of_compatible
    (S : TokenSystem H C T U P)
    (content : T → F)
    (Serious : H → F → Prop)
    (hcompat : LeviCompatible S content Serious)
    {h : H} {u : U} {p : P} {t : T}
    (hlive : PossLive S h u p t) :
    Serious h (content t) := by
  exact hcompat h u p t hlive.2

/-- A tiny witness showing that Serious alone need not provide a live token. -/
def seriousWithoutLiveSystem :
    TokenSystem Unit Unit Unit Unit Unit where
  origin := fun _ => ()
  committedAt := fun _ _ => True
  liveAdmissible := fun _ _ _ _ => False
  futureAllowed := fun _ _ _ _ => False
  closed := fun _ _ _ _ => False

def trivialContent : Unit → Unit := fun _ => ()
def trivialSerious : Unit → Unit → Prop := fun _ _ => True

theorem serious_does_not_imply_live :
    trivialSerious () (trivialContent ()) ∧
    ¬ PossLive seriousWithoutLiveSystem () () () () := by
  constructor
  · trivial
  · intro hlive
    exact hlive.2

/--
Hence the bridge is one-way in the intended direction: compatibility yields
Live -> Serious, while Serious -> Live is not valid without further assumptions.
-/
theorem levi_bridge_is_strictly_one_way :
    (LeviCompatible seriousWithoutLiveSystem trivialContent trivialSerious →
      ∀ {h u p t},
        PossLive seriousWithoutLiveSystem h u p t →
        trivialSerious h (trivialContent t)) ∧
    (trivialSerious () (trivialContent ()) ∧
      ¬ PossLive seriousWithoutLiveSystem () () () ()) := by
  constructor
  · intro hcompat h u p t hlive
    exact possLive_implies_serious_of_compatible
      seriousWithoutLiveSystem trivialContent trivialSerious hcompat hlive
  · exact serious_does_not_imply_live

end CPOG.LeviBridge
