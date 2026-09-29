namespace CPOG

/-!
# v57 philosophical bridge witnesses

Two central philosophical distinctions are given explicit witness theorems:

1. origin determines historical token individuation without forcing every
   semantic individuation;
2. static observation equivalence need not be dynamically safe.
-/

universe u v

def PayloadObservation
    {EventCode : Type u} {Payload : Type v} :
    Unit -> HistToken EventCode Payload -> Payload :=
  fun _ t => t.payload

theorem origin_individuation_with_semantic_deflation
    {EventCode : Type u} {Payload : Type v}
    {t1 t2 : HistToken EventCode Payload}
    (hOrigin : t1.origin ≠ t2.origin)
    (hPayload : t1.payload = t2.payload) :
    t1 ≠ t2 /\
    ObsEq PayloadObservation t1 t2 := by
  constructor
  · exact token_ne_of_origin_ne hOrigin
  · intro i
    cases i
    exact hPayload

/-! ## Static observation can be too coarse for dynamic safety -/

inductive StaticGapWorld where
  | left
  | right
  | leftFuture
  | rightFuture

deriving DecidableEq

inductive StaticGapAtom where
  | p

deriving DecidableEq

def staticGapG : Rel StaticGapWorld
  | .left, .leftFuture => True
  | .right, .rightFuture => True
  | _, _ => False

def staticGapId : Rel StaticGapWorld :=
  fun x y => x = y

def staticGapVal : StaticGapWorld -> StaticGapAtom -> Prop
  | .leftFuture, .p => True
  | _, _ => False

def staticGapModel : Model StaticGapWorld StaticGapAtom where
  val := staticGapVal
  rG := staticGapG
  rD := staticGapId
  rH := staticGapG

def staticAtomObservation :
    StaticGapAtom -> StaticGapWorld -> Bool
  | .p, w => if staticGapVal w .p then true else false

theorem static_gap_roots_observationally_equal :
    ObsEq staticAtomObservation
      StaticGapWorld.left StaticGapWorld.right := by
  intro a
  cases a
  rfl

theorem static_gap_leftFuture_positive :
    staticGapModel.val .leftFuture .p := by
  trivial

theorem static_gap_rightFuture_not_positive :
    Not (staticGapModel.val .rightFuture .p) := by
  intro h
  cases h

theorem static_gap_roots_not_bisimilar :
    Not (Bisimilar staticGapModel .left .right) := by
  intro hBis
  rcases hBis with ⟨Z, hZ, hLR⟩
  have hLeftStep : staticGapModel.rG .left .leftFuture := by
    trivial
  rcases hZ.forthG hLR hLeftStep with ⟨y, hRightStep, hRelated⟩
  have hy : y = StaticGapWorld.rightFuture := by
    cases y with
    | left => cases hRightStep
    | right => cases hRightStep
    | leftFuture => cases hRightStep
    | rightFuture => rfl
  subst y
  have hAtom :=
    (hZ.atom hRelated StaticGapAtom.p).mp
      static_gap_leftFuture_positive
  exact static_gap_rightFuture_not_positive hAtom

theorem static_observation_equivalence_not_dynamic_safety :
    ObsEq staticAtomObservation
      StaticGapWorld.left StaticGapWorld.right /\
    Not (Bisimilar staticGapModel
      StaticGapWorld.left StaticGapWorld.right) := by
  exact ⟨static_gap_roots_observationally_equal,
    static_gap_roots_not_bisimilar⟩

end CPOG
