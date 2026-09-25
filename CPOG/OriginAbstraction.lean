import CPOG.Origin
import CPOG.Provenance

/-!
Explicit consistency witness for the paper's slogan:
"Origin determines historical individuation, but not every semantic
individuation."
-/

namespace CPOG.OriginAbstraction

open CPOG.Possibility
open CPOG.Origin
open CPOG.SemanticProvenance

inductive Code where
  | c1 | c2
  deriving DecidableEq, Repr

inductive Token where
  | t1 | t2
  deriving DecidableEq, Repr

def S : TokenSystem Unit Code Token Unit Unit where
  origin
    | .t1 => .c1
    | .t2 => .c2
  committedAt := fun _ _ => True
  liveAdmissible := fun _ _ _ _ => True
  futureAllowed := fun _ _ _ _ => True
  closed := fun _ _ _ _ => False

def tokenOf : Code → Token
  | .c1 => .t1
  | .c2 => .t2

theorem tokenOf_is_origin_section : OriginSection S tokenOf := by
  intro c
  cases c <;> rfl

theorem tokens_are_historically_distinct : tokenOf .c1 ≠ tokenOf .c2 := by
  apply origin_individuation S tokenOf tokenOf_is_origin_section
  intro h
  cases h

/-- A deliberately coarse semantics that observes content/use but not origin. -/
def originBlindObservation : ObservationSystem Unit Token where
  Out := fun _ => Unit
  observe := fun _ _ => ()

theorem distinct_tokens_are_observation_equivalent :
    ObsEq originBlindObservation (tokenOf .c1) (tokenOf .c2) := by
  intro i
  cases i
  rfl

theorem distinct_tokens_merge_in_static_semantic_quotient :
    quotientMap originBlindObservation (tokenOf .c1) =
      quotientMap originBlindObservation (tokenOf .c2) := by
  exact (quotientMap_eq_iff_obsEq originBlindObservation
    (tokenOf .c1) (tokenOf .c2)).2
    distinct_tokens_are_observation_equivalent

/--
One theorem packages the philosophical point: the tokens are different because
their origins differ, yet an origin-blind semantics legitimately identifies
them.
-/
theorem origin_individuation_semantic_deflation :
    tokenOf .c1 ≠ tokenOf .c2 ∧
    S.origin (tokenOf .c1) ≠ S.origin (tokenOf .c2) ∧
    quotientMap originBlindObservation (tokenOf .c1) =
      quotientMap originBlindObservation (tokenOf .c2) := by
  refine ⟨tokens_are_historically_distinct, ?_, distinct_tokens_merge_in_static_semantic_quotient⟩
  intro h
  cases h

end CPOG.OriginAbstraction
