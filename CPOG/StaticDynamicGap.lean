import CPOG.ModalPreservation

namespace CPOG.StaticDynamicGap

open CPOG.ModalPreservation

inductive W where
  | x | y | z
  deriving DecidableEq, Repr

inductive Q where
  | merged | z
  deriving DecidableEq, Repr

inductive Atom where
  | p
  deriving DecidableEq, Repr

def sourceG : W -> W -> Prop
  | .x, .z => True
  | _, _ => False

def targetG : Q -> Q -> Prop
  | .merged, .z => True
  | _, _ => False

def eqRel {A : Type} : A -> A -> Prop := fun a b => a = b

def sourceModel : Model W Atom where
  G := sourceG
  D := eqRel
  H := eqRel
  val := fun _ _ => False

def q : W -> Q
  | .x => .merged
  | .y => .merged
  | .z => .z

def targetModel : Model Q Atom where
  G := targetG
  D := eqRel
  H := eqRel
  val := fun _ _ => False

theorem static_atoms_preserved (w : W) (a : Atom) :
    sourceModel.val w a <-> targetModel.val (q w) a := by
  simp [sourceModel, targetModel]

/--
The two source states x and y are statically indistinguishable by the current
atomic observation p, yet they have different G-futures.
-/
theorem x_y_statically_indistinguishable :
    forall a, sourceModel.val .x a <-> sourceModel.val .y a := by
  intro a
  simp [sourceModel]

/-- y vacuously satisfies box_G bottom because it has no G-successor. -/
theorem source_y_boxG_bottom :
    Sat sourceModel .y (.boxG .bot) := by
  intro v hv
  cases v <;> simp [sourceModel, sourceG] at hv

/-- The merged target state does not satisfy box_G bottom because it has a z-successor. -/
theorem target_merged_not_boxG_bottom :
    Not (Sat targetModel .merged (.boxG .bot)) := by
  intro h
  have hz : targetModel.G .merged .z := by
    simp [targetModel, targetG]
  exact h .z hz

theorem static_abstraction_changes_modal_truth :
    Sat sourceModel .y (.boxG .bot) /\
    Not (Sat targetModel (q .y) (.boxG .bot)) := by
  constructor
  · exact source_y_boxG_bottom
  · simpa [q] using target_merged_not_boxG_bottom

/-- Therefore atom preservation alone is insufficient for a dynamically safe abstraction. -/
theorem static_q_not_boundedMorphism :
    Not (BoundedMorphism sourceModel targetModel q) := by
  intro hm
  have hpres :=
    sat_iff_of_boundedMorphism hm (.boxG .bot) .y
  have htarget : Sat targetModel (q .y) (.boxG .bot) :=
    hpres.mp source_y_boxG_bottom
  exact static_abstraction_changes_modal_truth.2 htarget

end CPOG.StaticDynamicGap
