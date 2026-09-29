namespace CPOG

/-!
# v57 maximal dynamically safe quotient

For a fixed G/D/H model M, define dynamic bisimilarity as membership in some
bisimulation on M.  We prove that this is itself an equivalence relation and a
bisimulation, hence the greatest dynamically safe equivalence.  Its quotient
is therefore the coarsest quotient preserving all modal formulas in the
current language.
-/

universe u v

variable {W : Type u} {Atom : Type v}

def IdentityRel (W : Type u) : W -> W -> Prop :=
  fun x y => x = y

theorem identity_is_bisimulation (M : Model W Atom) :
    IsBisimulation M M (IdentityRel W) := by
  constructor
  · intro x y hxy a
    subst y
    rfl
  · intro x y hxy x' hxx'
    subst y
    exact ⟨x', hxx', rfl⟩
  · intro x y hxy y' hyy'
    subst y
    exact ⟨y', hyy', rfl⟩
  · intro x y hxy x' hxx'
    subst y
    exact ⟨x', hxx', rfl⟩
  · intro x y hxy y' hyy'
    subst y
    exact ⟨y', hyy', rfl⟩
  · intro x y hxy x' hxx'
    subst y
    exact ⟨x', hxx', rfl⟩
  · intro x y hxy y' hyy'
    subst y
    exact ⟨y', hyy', rfl⟩

def Converse {X : Type u} (Z : X -> X -> Prop) : X -> X -> Prop :=
  fun x y => Z y x

theorem converse_is_bisimulation
    (M : Model W Atom)
    {Z : W -> W -> Prop}
    (hZ : IsBisimulation M M Z) :
    IsBisimulation M M (Converse Z) := by
  constructor
  · intro x y hyx a
    exact (hZ.atom hyx a).symm
  · intro x y hyx x' hxx'
    rcases hZ.backG hyx hxx' with ⟨y', hyy', hy'x'⟩
    exact ⟨y', hyy', hy'x'⟩
  · intro x y hyx y' hyy'
    rcases hZ.forthG hyx hyy' with ⟨x', hxx', hy'x'⟩
    exact ⟨x', hxx', hy'x'⟩
  · intro x y hyx x' hxx'
    rcases hZ.backD hyx hxx' with ⟨y', hyy', hy'x'⟩
    exact ⟨y', hyy', hy'x'⟩
  · intro x y hyx y' hyy'
    rcases hZ.forthD hyx hyy' with ⟨x', hxx', hy'x'⟩
    exact ⟨x', hxx', hy'x'⟩
  · intro x y hyx x' hxx'
    rcases hZ.backH hyx hxx' with ⟨y', hyy', hy'x'⟩
    exact ⟨y', hyy', hy'x'⟩
  · intro x y hyx y' hyy'
    rcases hZ.forthH hyx hyy' with ⟨x', hxx', hy'x'⟩
    exact ⟨x', hxx', hy'x'⟩

def RelComp {X : Type u}
    (Z₁ Z₂ : X -> X -> Prop) : X -> X -> Prop :=
  fun x z => exists y, Z₁ x y /\ Z₂ y z

theorem compose_is_bisimulation
    (M : Model W Atom)
    {Z₁ Z₂ : W -> W -> Prop}
    (h₁ : IsBisimulation M M Z₁)
    (h₂ : IsBisimulation M M Z₂) :
    IsBisimulation M M (RelComp Z₁ Z₂) := by
  constructor
  · intro x z hxz a
    rcases hxz with ⟨y, hxy, hyz⟩
    exact Iff.trans (h₁.atom hxy a) (h₂.atom hyz a)
  · intro x z hxz x' hxx'
    rcases hxz with ⟨y, hxy, hyz⟩
    rcases h₁.forthG hxy hxx' with ⟨y', hyy', hx'y'⟩
    rcases h₂.forthG hyz hyy' with ⟨z', hzz', hy'z'⟩
    exact ⟨z', hzz', ⟨y', hx'y', hy'z'⟩⟩
  · intro x z hxz z' hzz'
    rcases hxz with ⟨y, hxy, hyz⟩
    rcases h₂.backG hyz hzz' with ⟨y', hyy', hy'z'⟩
    rcases h₁.backG hxy hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', ⟨y', hx'y', hy'z'⟩⟩
  · intro x z hxz x' hxx'
    rcases hxz with ⟨y, hxy, hyz⟩
    rcases h₁.forthD hxy hxx' with ⟨y', hyy', hx'y'⟩
    rcases h₂.forthD hyz hyy' with ⟨z', hzz', hy'z'⟩
    exact ⟨z', hzz', ⟨y', hx'y', hy'z'⟩⟩
  · intro x z hxz z' hzz'
    rcases hxz with ⟨y, hxy, hyz⟩
    rcases h₂.backD hyz hzz' with ⟨y', hyy', hy'z'⟩
    rcases h₁.backD hxy hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', ⟨y', hx'y', hy'z'⟩⟩
  · intro x z hxz x' hxx'
    rcases hxz with ⟨y, hxy, hyz⟩
    rcases h₁.forthH hxy hxx' with ⟨y', hyy', hx'y'⟩
    rcases h₂.forthH hyz hyy' with ⟨z', hzz', hy'z'⟩
    exact ⟨z', hzz', ⟨y', hx'y', hy'z'⟩⟩
  · intro x z hxz z' hzz'
    rcases hxz with ⟨y, hxy, hyz⟩
    rcases h₂.backH hyz hzz' with ⟨y', hyy', hy'z'⟩
    rcases h₁.backH hxy hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', ⟨y', hx'y', hy'z'⟩⟩

def DynamicBisimilar
    (M : Model W Atom) (x y : W) : Prop :=
  exists Z : W -> W -> Prop, IsBisimulation M M Z /\ Z x y

theorem dynamicBisimilar_refl
    (M : Model W Atom) :
    forall x, DynamicBisimilar M x x := by
  intro x
  exact ⟨IdentityRel W, identity_is_bisimulation M, rfl⟩

theorem dynamicBisimilar_symm
    (M : Model W Atom) :
    forall {x y}, DynamicBisimilar M x y -> DynamicBisimilar M y x := by
  intro x y h
  rcases h with ⟨Z, hZ, hxy⟩
  exact ⟨Converse Z, converse_is_bisimulation M hZ, hxy⟩

theorem dynamicBisimilar_trans
    (M : Model W Atom) :
    forall {x y z},
      DynamicBisimilar M x y ->
      DynamicBisimilar M y z ->
      DynamicBisimilar M x z := by
  intro x y z hxy hyz
  rcases hxy with ⟨Z₁, h₁, hxy₁⟩
  rcases hyz with ⟨Z₂, h₂, hyz₂⟩
  exact
    ⟨RelComp Z₁ Z₂,
      compose_is_bisimulation M h₁ h₂,
      ⟨y, hxy₁, hyz₂⟩⟩

theorem dynamicBisimilar_is_bisimulation
    (M : Model W Atom) :
    IsBisimulation M M (DynamicBisimilar M) := by
  constructor
  · intro x y hxy a
    rcases hxy with ⟨Z, hZ, h⟩
    exact hZ.atom h a
  · intro x y hxy x' hxx'
    rcases hxy with ⟨Z, hZ, h⟩
    rcases hZ.forthG h hxx' with ⟨y', hyy', hx'y'⟩
    exact ⟨y', hyy', ⟨Z, hZ, hx'y'⟩⟩
  · intro x y hxy y' hyy'
    rcases hxy with ⟨Z, hZ, h⟩
    rcases hZ.backG h hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', ⟨Z, hZ, hx'y'⟩⟩
  · intro x y hxy x' hxx'
    rcases hxy with ⟨Z, hZ, h⟩
    rcases hZ.forthD h hxx' with ⟨y', hyy', hx'y'⟩
    exact ⟨y', hyy', ⟨Z, hZ, hx'y'⟩⟩
  · intro x y hxy y' hyy'
    rcases hxy with ⟨Z, hZ, h⟩
    rcases hZ.backD h hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', ⟨Z, hZ, hx'y'⟩⟩
  · intro x y hxy x' hxx'
    rcases hxy with ⟨Z, hZ, h⟩
    rcases hZ.forthH h hxx' with ⟨y', hyy', hx'y'⟩
    exact ⟨y', hyy', ⟨Z, hZ, hx'y'⟩⟩
  · intro x y hxy y' hyy'
    rcases hxy with ⟨Z, hZ, h⟩
    rcases hZ.backH h hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', ⟨Z, hZ, hx'y'⟩⟩

theorem dynamicBisimilar_dynamicEquiv
    (M : Model W Atom) :
    DynamicEquiv M (DynamicBisimilar M) := by
  constructor
  · exact dynamicBisimilar_refl M
  · exact dynamicBisimilar_symm M
  · exact dynamicBisimilar_trans M
  · exact dynamicBisimilar_is_bisimulation M

theorem every_bisimulation_refines_dynamicBisimilar
    (M : Model W Atom)
    {Z : W -> W -> Prop}
    (hZ : IsBisimulation M M Z) :
    forall {x y}, Z x y -> DynamicBisimilar M x y := by
  intro x y hxy
  exact ⟨Z, hZ, hxy⟩

theorem every_dynamicEquiv_refines_dynamicBisimilar
    (M : Model W Atom)
    {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) :
    forall {x y}, E x y -> DynamicBisimilar M x y := by
  exact every_bisimulation_refines_dynamicBisimilar M hE.bisim

def dynamicBisimSetoid (M : Model W Atom) : Setoid W where
  r := DynamicBisimilar M
  iseqv :=
    ⟨dynamicBisimilar_refl M,
      dynamicBisimilar_symm M,
      dynamicBisimilar_trans M⟩

abbrev MaxDynamicQuotient (M : Model W Atom) :=
  Quotient (dynamicBisimSetoid M)

def maximalDynamicPresentation
    (M : Model W Atom) :
    QuotientPresentation W (MaxDynamicQuotient M) (DynamicBisimilar M) where
  classOf := fun x => Quotient.mk (dynamicBisimSetoid M) x
  surj := by
    intro q
    exact Quotient.exists_rep q
  class_eq_iff := by
    intro x y
    constructor
    · exact @Quotient.exact W (dynamicBisimSetoid M) x y
    · exact @Quotient.sound W (dynamicBisimSetoid M) x y

theorem maximal_dynamic_quotient_is_safe
    (M : Model W Atom) :
    IsBisimulation
      M
      (quotientModel M (maximalDynamicPresentation M))
      (ProjectionRel (maximalDynamicPresentation M)) := by
  exact projection_is_bisimulation
    (dynamicBisimilar_dynamicEquiv M)
    (maximalDynamicPresentation M)

theorem maximal_dynamic_quotient_truth_preservation
    (M : Model W Atom)
    (phi : Formula Atom) (x : W) :
    Satisfies M x phi <->
      Satisfies
        (quotientModel M (maximalDynamicPresentation M))
        ((maximalDynamicPresentation M).classOf x)
        phi := by
  exact quotient_invariance
    (dynamicBisimilar_dynamicEquiv M)
    (maximalDynamicPresentation M)
    phi x

theorem maximal_dynamic_quotient_is_coarsest
    (M : Model W Atom)
    {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) :
    forall {x y},
      E x y ->
      (maximalDynamicPresentation M).classOf x =
        (maximalDynamicPresentation M).classOf y := by
  intro x y hxy
  apply (maximalDynamicPresentation M).class_eq_iff.mpr
  exact every_dynamicEquiv_refines_dynamicBisimilar M hE hxy

end CPOG
