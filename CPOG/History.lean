import CPOG.Possibility

namespace CPOG.History

universe uC uV

variable {C : Type uC} {V : Type uV}

/-- Minimal append-only Core history: committed code/content records in successful order. -/
abbrev RawCoreHistory (C : Type uC) (V : Type uV) := List (C × V)

/-- A later history is obtained only by appending a finite tail. -/
def PrefixExtends (h k : RawCoreHistory C V) : Prop :=
  ∃ tail, k = h ++ tail

/-- Historical commitment is ordinary membership in the append-only Core log. -/
def CommittedAt (h : RawCoreHistory C V) (c : C) : Prop :=
  ∃ v, (c, v) ∈ h

/-- A particular historical content record occurred in the Core log. -/
def RecordedAt (h : RawCoreHistory C V) (c : C) (v : V) : Prop :=
  (c, v) ∈ h

theorem record_persistent_of_prefix
    {h k : RawCoreHistory C V}
    (hext : PrefixExtends h k)
    {c : C} {v : V}
    (hrec : RecordedAt h c v) :
    RecordedAt k c v := by
  rcases hext with ⟨tail, rfl⟩
  exact List.mem_append_left tail hrec

theorem committed_persistent_of_prefix
    {h k : RawCoreHistory C V}
    (hext : PrefixExtends h k)
    {c : C}
    (hcommit : CommittedAt h c) :
    CommittedAt k c := by
  rcases hcommit with ⟨v, hv⟩
  exact ⟨v, record_persistent_of_prefix hext hv⟩

/--
Historical Persistence: every committed code remains committed in every append-only extension,
and the original code/content record itself remains present.
-/
theorem historical_persistence
    {h k : RawCoreHistory C V}
    (hext : PrefixExtends h k)
    {c : C} {v : V}
    (hrec : RecordedAt h c v) :
    CommittedAt k c ∧ RecordedAt k c v := by
  have hp := record_persistent_of_prefix hext hrec
  exact ⟨⟨v, hp⟩, hp⟩

/-- Prefix extension is reflexive. -/
theorem prefixExtends_refl (h : RawCoreHistory C V) :
    PrefixExtends h h := by
  exact ⟨[], by simp⟩

/-- Prefix extension is transitive. -/
theorem prefixExtends_trans
    {h k m : RawCoreHistory C V}
    (hhk : PrefixExtends h k)
    (hkm : PrefixExtends k m) :
    PrefixExtends h m := by
  rcases hhk with ⟨t₁, rfl⟩
  rcases hkm with ⟨t₂, rfl⟩
  exact ⟨t₁ ++ t₂, by simp [List.append_assoc]⟩

/-- The induced raw-history accessibility is therefore an S4 preorder. -/
theorem prefix_frame_S4 :
    (∀ h : RawCoreHistory C V, PrefixExtends h h) ∧
    (∀ h k m : RawCoreHistory C V,
      PrefixExtends h k → PrefixExtends k m → PrefixExtends h m) := by
  constructor
  · exact prefixExtends_refl
  · intro h k m hhk hkm
    exact prefixExtends_trans hhk hkm

end CPOG.History
