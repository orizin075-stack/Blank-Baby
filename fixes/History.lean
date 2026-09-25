import CPOG.Theory

namespace CPOG.History

variable {A : Type}

abbrev Prefix : List A → List A → Prop := CPOG.EpistemicPotentialism.Theory.Prefix

/-- The raw history accessibility relation is reflexive. -/
theorem prefix_reflexive : ∀ h : List A, Prefix h h := by
  intro h
  exact CPOG.EpistemicPotentialism.Theory.prefix_refl h

/-- The raw history accessibility relation is transitive. -/
theorem prefix_transitive :
    ∀ ⦃h k l : List A⦄, Prefix h k → Prefix k l → Prefix h l := by
  intro h k l hhk hkl
  exact CPOG.EpistemicPotentialism.Theory.prefix_trans hhk hkl

/-- A committed event/action remains in every prefix extension. -/
theorem membership_persists {a : A} {h k : List A}
    (hext : Prefix h k) (hmem : a ∈ h) : a ∈ k := by
  rcases hext with ⟨tail, rfl⟩
  simp only [List.mem_append]
  exact Or.inl hmem

/-- A predicate that is monotone under prefix extension is historically persistent. -/
def Persistent (P : List A → Prop) : Prop :=
  ∀ ⦃h k⦄, Prefix h k → P h → P k

/-- Membership of a fixed committed item is a persistent history predicate. -/
theorem committed_predicate_persistent (a : A) :
    Persistent (fun h : List A => a ∈ h) := by
  intro h k hext hmem
  exact membership_persists hext hmem

/-- The prefix history frame satisfies the S4 frame conditions (reflexivity + transitivity). -/
theorem prefix_frame_S4 :
    (∀ h : List A, Prefix h h) ∧
    (∀ ⦃h k l : List A⦄, Prefix h k → Prefix k l → Prefix h l) := by
  exact ⟨prefix_reflexive, prefix_transitive⟩

end CPOG.History
