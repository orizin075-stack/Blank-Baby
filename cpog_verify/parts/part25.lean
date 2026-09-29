namespace CPOG

/-!
# v57 philosophical bridge witnesses

Two small witnesses connect the formal architecture to the paper's central
philosophical distinctions.

1. Origin individuation does not force every semantic individuation:
   two tokens with different origins are historically distinct while an
   origin-blind payload observation identifies them.

2. Static observational agreement is weaker than dynamic safety:
   two worlds can agree on every current atom while failing dynamic
   bisimilarity because their futures differ.
-/

inductive OriginWitnessEvent where
  | alpha
  | beta

deriving DecidableEq

def originWitnessA : HistToken OriginWitnessEvent Unit :=
  ⟨.alpha, ()⟩

def originWitnessB : HistToken OriginWitnessEvent Unit :=
  ⟨.beta, ()⟩

def payloadOnlyObservation :
    Unit -> HistToken OriginWitnessEvent Unit -> Unit :=
  fun _ t => t.payload

theorem origin_witness_distinct :
    originWitnessA ≠ originWitnessB := by
  apply token_ne_of_origin_ne
  intro h
  cases h

theorem origin_blind_observation_identifies_witnesses :
    ObsEq payloadOnlyObservation originWitnessA originWitnessB := by
  intro i
  cases i
  rfl

theorem origin_individuation_semantic_deflation_witness :
    originWitnessA ≠ originWitnessB /\
    ObsEq payloadOnlyObservation originWitnessA originWitnessB :=
  ⟨origin_witness_distinct,
    origin_blind_observation_identifies_witnesses⟩

def StaticAtomEq
    {W : Type u} {Atom : Type v}
    (M : Model W Atom) (x y : W) : Prop :=
  forall a, M.val x a <-> M.val y a

inductive StaticDynamicWorld where
  | x
  | y
  | z

deriving DecidableEq

inductive StaticDynamicAtom where
  | p

deriving DecidableEq

def staticDynamicGR : Rel StaticDynamicWorld
  | .x, .z => True
  | _, _ => False

def staticDynamicEmpty : Rel StaticDynamicWorld :=
  fun _ _ => False

def staticDynamicVal :
    StaticDynamicWorld -> StaticDynamicAtom -> Prop
  | .z, .p => True
  | _, _ => False

def staticDynamicModel :
    Model StaticDynamicWorld StaticDynamicAtom where
  val := staticDynamicVal
  rG := staticDynamicGR
  rD := staticDynamicEmpty
  rH := staticDynamicEmpty

theorem staticDynamic_current_atoms_agree :
    StaticAtomEq staticDynamicModel .x .y := by
  intro a
  cases a
  constructor <;> intro h <;> cases h

theorem staticDynamic_not_bisimilar :
    Not (DynamicBisimilar staticDynamicModel .x .y) := by
  intro hxy
  have hB :
      IsBisimulation
        staticDynamicModel
        staticDynamicModel
        (DynamicBisimilar staticDynamicModel) :=
    dynamicBisimilar_is_bisimulation staticDynamicModel
  have hxz : staticDynamicModel.rG .x .z := by
    trivial
  rcases hB.forthG hxy hxz with ⟨y', hyy', _⟩
  cases y' <;> cases hyy'

theorem static_observation_not_dynamic_safety_witness :
    StaticAtomEq staticDynamicModel .x .y /\
    Not (DynamicBisimilar staticDynamicModel .x .y) :=
  ⟨staticDynamic_current_atoms_agree,
    staticDynamic_not_bisimilar⟩

end CPOG
