import CPOG.Possibility

namespace CPOG.Origin

open CPOG.Possibility

universe uH uC uT uU uP

variable {H : Type uH} {C : Type uC} {T : Type uT}
variable {U : Type uU} {P : Type uP}

/--
A canonical token constructor is a section of the token-origin map:
each event/code c has a designated token whose origin is exactly c.
-/
def OriginSection
    (S : TokenSystem H C T U P) (tokenOf : C -> T) : Prop :=
  forall c, S.origin (tokenOf c) = c

/-- Different origins force different tokens, for any token system. -/
theorem distinct_origins_imply_distinct_tokens
    (S : TokenSystem H C T U P)
    {t₁ t₂ : T}
    (h : S.origin t₁ ≠ S.origin t₂) :
    t₁ ≠ t₂ := by
  intro hEq
  apply h
  exact congrArg S.origin hEq

/--
Origin individuation in the paper's canonical-token notation:
if tokenOf is a section of origin, distinct EventCodes yield distinct Tokens.
-/
theorem origin_individuation
    (S : TokenSystem H C T U P)
    (tokenOf : C -> T)
    (hsection : OriginSection S tokenOf)
    {c₁ c₂ : C}
    (hne : c₁ ≠ c₂) :
    tokenOf c₁ ≠ tokenOf c₂ := by
  intro hEq
  apply hne
  calc
    c₁ = S.origin (tokenOf c₁) := (hsection c₁).symm
    _ = S.origin (tokenOf c₂) := congrArg S.origin hEq
    _ = c₂ := hsection c₂


/--
A successful commitment of EventCode c makes its canonical token historically
possible.  This is the formal recognition-event -> historical-token bridge.
-/
theorem commit_generates_canonical_historical_token
    (S : TokenSystem H C T U P)
    (tokenOf : C -> T)
    (hsection : OriginSection S tokenOf)
    {h : H} {c : C}
    (hcommit : S.committedAt h c) :
    PossHist S h (tokenOf c) := by
  change S.committedAt h (S.origin (tokenOf c))
  simpa [hsection c] using hcommit

/--
For a canonical token, historical possibility is exactly commitment of its
origin EventCode.
-/
theorem canonical_historical_token_iff_committed
    (S : TokenSystem H C T U P)
    (tokenOf : C -> T)
    (hsection : OriginSection S tokenOf)
    {h : H} {c : C} :
    PossHist S h (tokenOf c) <-> S.committedAt h c := by
  change S.committedAt h (S.origin (tokenOf c)) <-> S.committedAt h c
  rw [hsection c]

end CPOG.Origin
