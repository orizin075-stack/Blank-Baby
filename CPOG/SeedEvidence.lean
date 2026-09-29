import CPOG.Check
import CPOG.Possibility

namespace CPOG.SeedEvidence

open CPOG.EpistemicPotentialism
open CPOG.Possibility

/-- Standard-kind tags used only for the explicit default seed policy below. -/
inductive StandardKind where
  | directObservation
  | dream
  | imagination
  | hypothesis
  deriving DecidableEq, Repr

/--
A conservative default seed policy:
direct observation may seed positive support, while dream/imagination/hypothesis
introduce a historical candidate without positive or negative evidential support.
-/
def defaultSeed : StandardKind -> Evidence
  | .directObservation => evT
  | .dream => evN
  | .imagination => evN
  | .hypothesis => evN

theorem dream_seed_is_neither : defaultSeed .dream = evN := rfl
theorem imagination_seed_is_neither : defaultSeed .imagination = evN := rfl
theorem hypothesis_seed_is_neither : defaultSeed .hypothesis = evN := rfl
theorem observation_seed_is_positive : defaultSeed .directObservation = evT := rfl

theorem dream_seed_not_positiveOnly :
    positiveOnly (defaultSeed .dream) = false := rfl

/-- Minimal token system witnessing that live possibility need not carry positive evidence. -/
def dreamTokenSystem : TokenSystem Unit Unit Unit Unit Unit where
  origin := fun _ => ()
  committedAt := fun _ _ => True
  liveAdmissible := fun _ _ _ _ => True
  futureAllowed := fun _ _ _ _ => True
  closed := fun _ _ _ _ => False

/--
A dream-token can be historically generated and currently live while its default
evidence remains N. This formally separates possibility generation from belief/evidence generation.
-/
theorem dream_can_be_live_with_no_positive_support :
    PossLive dreamTokenSystem () () () () /\
    defaultSeed .dream = evN /\
    positiveOnly (defaultSeed .dream) = false := by
  exact ⟨⟨True.intro, True.intro⟩, rfl, rfl⟩

end CPOG.SeedEvidence
