import CPOG.General

namespace CPOG.DynamicSafety

universe uN uB
variable {N : Type uN} {B : Type uB}

def SupportStep (E : N → N → Prop) (S : N → Prop) (x : N) : Prop :=
  S x ∨ ∃ y, E y x ∧ S y

def SupportBlockConsistent (block : N → B) (S : N → Prop) : Prop :=
  ∀ x y, block x = block y → (S x ↔ S y)

def EffectiveIncomingSimulation
    (E : N → N → Prop) (block : N → B) (left right : N) : Prop :=
  ∀ source,
    E source left →
    block source ≠ block left →
    ∃ source', E source' right ∧ block source' = block source

def StructuralLumpable (E : N → N → Prop) (block : N → B) : Prop :=
  ∀ left right,
    block left = block right →
    EffectiveIncomingSimulation E block left right ∧
      EffectiveIncomingSimulation E block right left

def SupportDynamicsStable (E : N → N → Prop) (block : N → B) : Prop :=
  ∀ S,
    SupportBlockConsistent block S →
    SupportBlockConsistent block (SupportStep E S)

theorem structural_implies_support_stable
    (E : N → N → Prop) (block : N → B)
    (hlump : StructuralLumpable E block) :
    SupportDynamicsStable E block := by
  intro S hS left right hblock
  have hsims := hlump left right hblock
  constructor
  · intro hleft
    rcases hleft with hbase | ⟨source, hE, hsrc⟩
    · left
      exact (hS left right hblock).mp hbase
    · by_cases hself : block source = block left
      · left
        have hsourceLeft : S left := (hS source left hself).mp hsrc
        exact (hS left right hblock).mp hsourceLeft
      · right
        rcases hsims.1 source hE hself with ⟨source', hE', hblockSrc⟩
        refine ⟨source', hE', ?_⟩
        exact (hS source' source hblockSrc).mpr hsrc
  · intro hright
    rcases hright with hbase | ⟨source, hE, hsrc⟩
    · left
      exact (hS left right hblock).mpr hbase
    · by_cases hself : block source = block right
      · left
        have hsourceRight : S right := (hS source right hself).mp hsrc
        exact (hS left right hblock).mpr hsourceRight
      · right
        rcases hsims.2 source hE hself with ⟨source', hE', hblockSrc⟩
        refine ⟨source', hE', ?_⟩
        exact (hS source' source hblockSrc).mpr hsrc

theorem support_stable_implies_structural
    (E : N → N → Prop) (block : N → B)
    (hstable : SupportDynamicsStable E block) :
    StructuralLumpable E block := by
  intro left right hblock
  constructor
  · intro source hE hnonself
    let S : N → Prop := fun z => block z = block source
    have hS : SupportBlockConsistent block S := by
      intro x y hxy
      constructor <;> intro h
      · exact hxy.symm.trans h
      · exact hxy.trans h
    have hpost := hstable S hS left right hblock
    have hleft : SupportStep E S left := by
      right
      exact ⟨source, hE, rfl⟩
    have hright : SupportStep E S right := hpost.mp hleft
    rcases hright with hbase | ⟨source', hE', hblockSrc⟩
    · exfalso
      apply hnonself
      exact hbase.symm.trans hblock.symm
    · exact ⟨source', hE', hblockSrc⟩
  · intro source hE hnonself
    let S : N → Prop := fun z => block z = block source
    have hS : SupportBlockConsistent block S := by
      intro x y hxy
      constructor <;> intro h
      · exact hxy.symm.trans h
      · exact hxy.trans h
    have hpost := hstable S hS right left hblock.symm
    have hright : SupportStep E S right := by
      right
      exact ⟨source, hE, rfl⟩
    have hleft : SupportStep E S left := hpost.mp hright
    rcases hleft with hbase | ⟨source', hE', hblockSrc⟩
    · exfalso
      apply hnonself
      exact hbase.symm.trans hblock
    · exact ⟨source', hE', hblockSrc⟩

theorem structural_iff_support_stable
    (E : N → N → Prop) (block : N → B) :
    StructuralLumpable E block ↔ SupportDynamicsStable E block := by
  constructor
  · exact structural_implies_support_stable E block
  · exact support_stable_implies_structural E block

def EStar (E : N → N → Prop) (source target : N) : Prop :=
  source = target ∨ E source target

def ReflexiveClosureStable (E : N → N → Prop) (block : N → B) : Prop :=
  ∀ left right,
    block left = block right →
    ∀ b,
      (∃ source, EStar E source left ∧ block source = b) ↔
      (∃ source, EStar E source right ∧ block source = b)

theorem structural_implies_reflexiveClosureStable
    (E : N → N → Prop) (block : N → B)
    (hlump : StructuralLumpable E block) :
    ReflexiveClosureStable E block := by
  intro left right hblock b
  have hsims := hlump left right hblock
  constructor
  · rintro ⟨source, hstar, hsrcBlock⟩
    rcases hstar with rfl | hE
    · exact ⟨right, Or.inl rfl, hblock.symm.trans hsrcBlock⟩
    · by_cases hself : block source = block left
      · exact ⟨right, Or.inl rfl, hblock.symm.trans (hself.symm.trans hsrcBlock)⟩
      · rcases hsims.1 source hE hself with ⟨source', hE', hEq⟩
        exact ⟨source', Or.inr hE', hEq.trans hsrcBlock⟩
  · rintro ⟨source, hstar, hsrcBlock⟩
    rcases hstar with rfl | hE
    · exact ⟨left, Or.inl rfl, hblock.trans hsrcBlock⟩
    · by_cases hself : block source = block right
      · exact ⟨left, Or.inl rfl, hblock.trans (hself.symm.trans hsrcBlock)⟩
      · rcases hsims.2 source hE hself with ⟨source', hE', hEq⟩
        exact ⟨source', Or.inr hE', hEq.trans hsrcBlock⟩

theorem reflexiveClosureStable_implies_structural
    (E : N → N → Prop) (block : N → B)
    (hstable : ReflexiveClosureStable E block) :
    StructuralLumpable E block := by
  intro left right hblock
  constructor
  · intro source hE hnonself
    have hleft : ∃ s, EStar E s left ∧ block s = block source :=
      ⟨source, Or.inr hE, rfl⟩
    have hright := (hstable left right hblock (block source)).mp hleft
    rcases hright with ⟨source', hstar, hEq⟩
    rcases hstar with hRefl | hEdge
    · subst source'
      exfalso
      apply hnonself
      exact hEq.symm.trans hblock.symm
    · exact ⟨source', hEdge, hEq⟩
  · intro source hE hnonself
    have hright : ∃ s, EStar E s right ∧ block s = block source :=
      ⟨source, Or.inr hE, rfl⟩
    have hleft := (hstable left right hblock (block source)).mpr hright
    rcases hleft with ⟨source', hstar, hEq⟩
    rcases hstar with hRefl | hEdge
    · subst source'
      exfalso
      apply hnonself
      exact hEq.symm.trans hblock
    · exact ⟨source', hEdge, hEq⟩

theorem structural_iff_reflexiveClosureStable
    (E : N → N → Prop) (block : N → B) :
    StructuralLumpable E block ↔ ReflexiveClosureStable E block := by
  constructor
  · exact structural_implies_reflexiveClosureStable E block
  · exact reflexiveClosureStable_implies_structural E block

abbrev PropEvidence (N : Type uN) := N → Prop × Prop

def FDEBlockConsistent (block : N → B) (σ : PropEvidence N) : Prop :=
  SupportBlockConsistent block (fun x => (σ x).1) ∧
  SupportBlockConsistent block (fun x => (σ x).2)

def FDEStep (E : N → N → Prop) (σ : PropEvidence N) : PropEvidence N :=
  fun x =>
    (SupportStep E (fun y => (σ y).1) x,
     SupportStep E (fun y => (σ y).2) x)

def FDEDynamicsStable (E : N → N → Prop) (block : N → B) : Prop :=
  ∀ σ, FDEBlockConsistent block σ → FDEBlockConsistent block (FDEStep E σ)

theorem structural_implies_FDE_stable
    (E : N → N → Prop) (block : N → B)
    (hlump : StructuralLumpable E block) :
    FDEDynamicsStable E block := by
  intro σ hσ
  constructor
  · exact (structural_implies_support_stable E block hlump)
      (fun x => (σ x).1) hσ.1
  · exact (structural_implies_support_stable E block hlump)
      (fun x => (σ x).2) hσ.2

theorem FDE_stable_implies_structural
    (E : N → N → Prop) (block : N → B)
    (hstable : FDEDynamicsStable E block) :
    StructuralLumpable E block := by
  apply support_stable_implies_structural E block
  intro S hS
  let σ : PropEvidence N := fun x => (S x, False)
  have hσ : FDEBlockConsistent block σ := by
    constructor
    · exact hS
    · intro x y hxy
      constructor <;> intro h <;> contradiction
  have hpost := (hstable σ hσ).1
  simpa [σ, FDEStep] using hpost

theorem structural_iff_FDE_stable
    (E : N → N → Prop) (block : N → B) :
    StructuralLumpable E block ↔ FDEDynamicsStable E block := by
  constructor
  · exact structural_implies_FDE_stable E block
  · exact FDE_stable_implies_structural E block

theorem dynamicSafety_iff_reflexiveClosureStability
    (E : N → N → Prop) (block : N → B) :
    FDEDynamicsStable E block ↔ ReflexiveClosureStable E block := by
  constructor
  · intro h
    exact structural_implies_reflexiveClosureStable E block
      (FDE_stable_implies_structural E block h)
  · intro h
    exact structural_implies_FDE_stable E block
      (reflexiveClosureStable_implies_structural E block h)

end CPOG.DynamicSafety
