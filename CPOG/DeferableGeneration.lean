import CPOG.General

namespace CPOG.DeferableGeneration

open CPOG.EpistemicPotentialism

/--
Two independent one-shot generation capabilities.  A state records which
capabilities have already been realized.
-/
structure State where
  seenA : Bool
  seenB : Bool
  deriving DecidableEq, Repr

/-- Generation is monotone: realized capabilities are never lost. -/
def G (x y : State) : Prop :=
  (x.seenA = true → y.seenA = true) ∧
  (x.seenB = true → y.seenB = true)

/-- The common extension that realizes everything realized by either branch. -/
def join (x y : State) : State :=
  ⟨x.seenA || y.seenA, x.seenB || y.seenB⟩

theorem left_reaches_join (x y : State) : G x (join x y) := by
  constructor
  · intro hx
    simp [join, hx]
  · intro hx
    simp [join, hx]

theorem right_reaches_join (x y : State) : G y (join x y) := by
  constructor
  · intro hy
    simp [join, hy]
  · intro hy
    simp [join, hy]

/-- Every two G-successors admit a common G-successor. -/
theorem generation_is_directed_at (w : State) :
    DirectedAt G w := by
  intro x y _ _
  exact ⟨join x y, left_reaches_join x y, right_reaches_join x y⟩

/--
Canonical deferable-generation witness: every instance of the .2 schema holds.
The proof uses only the existence of the common join extension.
-/
theorem deferable_generation_validates_dotTwo
    (phi : State → Prop) (w : State) :
    DotTwoR G phi w :=
  dotTwo_of_directedAt G phi w (generation_is_directed_at w)

end CPOG.DeferableGeneration
