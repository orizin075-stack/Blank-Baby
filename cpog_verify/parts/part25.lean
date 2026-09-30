namespace CPOG

/-!
# v57 semantic quotient, origin individuation, and static/dynamic gap
-/

universe u v w

def observationSetoid
    {I : Type u} {X : Type v} {Y : Type w}
    (O : I -> X -> Y) : Setoid X where
  r := ObsEq O
  iseqv := ⟨obsEq_refl O, obsEq_symm O, obsEq_trans O⟩

abbrev ObservationQuotient
    {I : Type u} {X : Type v} {Y : Type w}
    (O : I -> X -> Y) :=
  Quotient (observationSetoid O)

def observationClassOf
    {I : Type u} {X : Type v} {Y : Type w}
    (O : I -> X -> Y) (x : X) :
    ObservationQuotient O :=
  Quotient.mk (observationSetoid O) x

theorem observationClass_eq_iff_obsEq
    {I : Type u} {X : Type v} {Y : Type w}
    (O : I -> X -> Y) (x y : X) :
    observationClassOf O x = observationClassOf O y <->
      ObsEq O x y := by
  constructor
  · exact Quotient.exact
  · exact Quotient.sound

/--
Static semantic minimality in quotient form:
any equivalence that preserves every selected observation identifies only pairs
already identified by the observation quotient.
-/
theorem observation_quotient_is_coarsest_observation_preserving
    {I : Type u} {X : Type v} {Y : Type w}
    (O : I -> X -> Y)
    (E : X -> X -> Prop)
    (hPres : forall {x y}, E x y -> forall i, O i x = O i y) :
    forall {x y}, E x y ->
      observationClassOf O x = observationClassOf O y := by
  intro x y hxy
  apply (observationClass_eq_iff_obsEq O x y).mpr
  exact semantic_minimal_quotient O E hPres hxy

/-! ## Origin individuation with semantic deflation -/

inductive OriginWitnessCode where
  | c1
  | c2
deriving DecidableEq

def originWitnessToken1 : HistToken OriginWitnessCode Unit :=
  ⟨.c1, ()⟩

def originWitnessToken2 : HistToken OriginWitnessCode Unit :=
  ⟨.c2, ()⟩

def originBlindObservation :
    Unit -> HistToken OriginWitnessCode Unit -> Unit :=
  fun _ _ => ()

theorem originWitness_origins_distinct :
    originWitnessToken1.origin ≠ originWitnessToken2.origin := by
  decide

theorem originWitness_tokens_distinct :
    originWitnessToken1 ≠ originWitnessToken2 :=
  token_ne_of_origin_ne originWitness_origins_distinct

theorem originWitness_observation_equivalent :
    ObsEq originBlindObservation
      originWitnessToken1 originWitnessToken2 := by
  intro i
  cases i
  rfl

theorem originWitness_merge_in_semantic_quotient :
    observationClassOf originBlindObservation originWitnessToken1 =
      observationClassOf originBlindObservation originWitnessToken2 := by
  exact
    (observationClass_eq_iff_obsEq
      originBlindObservation originWitnessToken1 originWitnessToken2).mpr
      originWitness_observation_equivalent

/--
Origin determines historical individuation, but not every semantic
individuation: the same witness simultaneously has distinct origins, distinct
historical tokens, and equality in an origin-blind semantic quotient.
-/
theorem origin_individuation_semantic_deflation :
    originWitnessToken1.origin ≠ originWitnessToken2.origin /\
    originWitnessToken1 ≠ originWitnessToken2 /\
    observationClassOf originBlindObservation originWitnessToken1 =
      observationClassOf originBlindObservation originWitnessToken2 := by
  exact
    ⟨originWitness_origins_distinct,
      originWitness_tokens_distinct,
      originWitness_merge_in_semantic_quotient⟩

/-! ## Static observation equivalence need not be dynamically safe -/

inductive StaticGapWorld where
  | x
  | y
  | z
deriving DecidableEq

inductive StaticGapAtom where
  | p
deriving DecidableEq

def staticGapG : Rel StaticGapWorld
  | .x, .z => True
  | _, _ => False

def staticGapId : Rel StaticGapWorld :=
  fun a b => a = b

def staticGapModel : Model StaticGapWorld StaticGapAtom where
  val := fun _ _ => False
  rG := staticGapG
  rD := staticGapId
  rH := staticGapId

def staticGapObservation : Unit -> StaticGapWorld -> Unit :=
  fun _ _ => ()

theorem staticGap_x_y_observation_equivalent :
    ObsEq staticGapObservation .x .y := by
  intro i
  cases i
  rfl

theorem staticGap_y_boxG_bottom :
    Satisfies staticGapModel .y (.boxG .bot) := by
  intro v hyv
  cases v <;> simp [staticGapModel, staticGapG] at hyv

theorem staticGap_x_not_boxG_bottom :
    Not (Satisfies staticGapModel .x (.boxG .bot)) := by
  intro h
  have hxz : staticGapModel.rG .x .z := by
    trivial
  exact h .z hxz

theorem staticGap_no_bisimulation_identifies_x_y
    {E : StaticGapWorld -> StaticGapWorld -> Prop}
    (hE : DynamicEquiv staticGapModel E) :
    Not (E .x .y) := by
  intro hxy
  have hiff :=
    bisimulation_invariance hE.bisim (.boxG .bot) hxy
  have hy : Satisfies staticGapModel .y (.boxG .bot) :=
    staticGap_y_boxG_bottom
  have hx : Satisfies staticGapModel .x (.boxG .bot) :=
    hiff.mpr hy
  exact staticGap_x_not_boxG_bottom hx

theorem static_observation_equivalence_not_dynamically_safe :
    ObsEq staticGapObservation .x .y /\
    Not (ObsBisimilar staticGapModel staticGapObservation .x .y) := by
  constructor
  · exact staticGap_x_y_observation_equivalent
  · intro h
    rcases h with ⟨B, hB⟩
    let E : StaticGapWorld -> StaticGapWorld -> Prop := B.Z
    let hDyn : DynamicEquiv staticGapModel E :=
      { refl := by
          intro a
          exact (obsBisimilar_refl staticGapModel staticGapObservation a).choose_spec
        symm := by
          intro a b hab
          have : ObsBisimilar staticGapModel staticGapObservation a b :=
            ⟨B, hab⟩
          rcases obsBisimilar_symm this with ⟨C, hC⟩
          -- We only need a contradiction below; use modal invariance of B directly.
          exact False.elim (by
            have hiff :=
              bisimulation_invariance B.bisim (.boxG .bot) hab
            exact staticGap_x_not_boxG_bottom
              (hiff.mpr staticGap_y_boxG_bottom))
        trans := by
          intro a b c hab hbc
          exact False.elim (by
            have hiff :=
              bisimulation_invariance B.bisim (.boxG .bot) hB
            exact staticGap_x_not_boxG_bottom
              (hiff.mpr staticGap_y_boxG_bottom))
        bisim := B.bisim }
    exact staticGap_no_bisimulation_identifies_x_y hDyn hB

/--
A cleaner direct form of the same gap, avoiding any quotient implementation:
x and y agree on every selected static observation, yet any observation-safe
bisimulation that related them would contradict the modal formula box_G bottom.
-/
theorem static_dynamic_gap_direct :
    ObsEq staticGapObservation .x .y /\
    forall B : ObservationBisimulation staticGapModel staticGapObservation,
      Not (B.Z .x .y) := by
  constructor
  · exact staticGap_x_y_observation_equivalent
  · intro B hxy
    have hiff :=
      bisimulation_invariance B.bisim (.boxG .bot) hxy
    exact staticGap_x_not_boxG_bottom
      (hiff.mpr staticGap_y_boxG_bottom)

end CPOG
