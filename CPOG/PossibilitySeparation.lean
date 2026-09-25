import CPOG.Possibility

namespace CPOG.PossibilitySeparation

open CPOG.Possibility

inductive H where
  | now
  | future
  deriving DecidableEq, Repr

/--
Fixed code space with future generation:
the token code is already nameable at now, but commitment starts only at future.
-/
def futureGenerationSystem : TokenSystem H Unit Unit Unit Unit where
  origin := fun _ => ()
  committedAt := fun h _ =>
    match h with
    | .now => False
    | .future => True
  liveAdmissible := fun h _ _ _ =>
    match h with
    | .now => False
    | .future => True
  futureAllowed := fun _ _ h h' =>
    h = .now /\ h' = .future
  closed := fun _ _ _ _ => False

theorem code_can_be_reachable_before_historical_generation :
    Not (PossHist futureGenerationSystem .now ()) /\
    PossReach futureGenerationSystem .now () () () := by
  constructor
  · intro h
    exact h
  · refine ⟨.future, ?_, ?_⟩
    · exact ⟨rfl, rfl⟩
    · exact ⟨True.intro, True.intro⟩

/--
A committed historical token can be excluded from current live use and from every
allowed future live state.
-/
def closedHistoricalSystem : TokenSystem Unit Unit Unit Unit Unit where
  origin := fun _ => ()
  committedAt := fun _ _ => True
  liveAdmissible := fun _ _ _ _ => False
  futureAllowed := fun _ _ _ _ => True
  closed := fun _ _ _ _ => True

theorem historical_need_not_be_live :
    PossHist closedHistoricalSystem () () /\
    Not (PossLive closedHistoricalSystem () () () ()) := by
  constructor
  · exact True.intro
  · intro h
    exact h.2

theorem historical_need_not_be_reachable :
    PossHist closedHistoricalSystem () () /\
    Not (PossReach closedHistoricalSystem () () () ()) := by
  constructor
  · exact True.intro
  · rintro ⟨h', _, hlive⟩
    exact hlive.2

/--
Together, these witnesses show that historical existence and future epistemic
reachability are logically independent in the intended direction:
reach can precede current historical generation of a fixed code, and historical
generation need not imply future live reachability.
-/
theorem hist_and_reach_do_not_collapse :
    (Not (PossHist futureGenerationSystem .now ()) /\
      PossReach futureGenerationSystem .now () () ()) /\
    (PossHist closedHistoricalSystem () () /\
      Not (PossReach closedHistoricalSystem () () () ())) := by
  exact ⟨code_can_be_reachable_before_historical_generation,
    historical_need_not_be_reachable⟩

end CPOG.PossibilitySeparation
