namespace CPOG

/-!
# v57 maximal dynamic bisimilarity quotient

DynamicEquiv already guarantees that a chosen quotient is modally safe.
This section constructs the coarsest such quotient: bisimilarity, defined as
membership in some G/D/H bisimulation.  Bisimilarity is itself an equivalence
and a bisimulation, every bisimulation refines it, and its quotient preserves
all formulas of the G/D/H modal language.
-/

universe u v w x

def IdRel {W : Type u} : W -> W -> Prop :=
  fun a b => a = b

theorem identity_is_bisimulation
    {W : Type u} {Atom : Type v}
    (M : Model W Atom) :
    IsBisimulation M M IdRel := by
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

def Converse
    {W1 : Type u} {W2 : Type v}
    (Z : W1 -> W2 -> Prop) : W2 -> W1 -> Prop :=
  fun y x => Z x y

theorem converse_is_bisimulation
    {W1 : Type u} {W2 : Type v} {Atom : Type w}
    {M1 : Model W1 Atom} {M2 : Model W2 Atom}
    {Z : W1 -> W2 -> Prop}
    (hZ : IsBisimulation M1 M2 Z) :
    IsBisimulation M2 M1 (Converse Z) := by
  constructor
  · intro y x hyx a
    exact (hZ.atom hyx a).symm
  · intro y x hyx y' hyy'
    rcases hZ.backG hyx hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', hx'y'⟩
  · intro y x hyx x' hxx'
    rcases hZ.forthG hyx hxx' with ⟨y', hyy', hx'y'⟩
    exact ⟨y', hyy', hx'y'⟩
  · intro y x hyx y' hyy'
    rcases hZ.backD hyx hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', hx'y'⟩
  · intro y x hyx x' hxx'
    rcases hZ.forthD hyx hxx' with ⟨y', hyy', hx'y'⟩
    exact ⟨y', hyy', hx'y'⟩
  · intro y x hyx y' hyy'
    rcases hZ.backH hyx hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', hx'y'⟩
  · intro y x hyx x' hxx'
    rcases hZ.forthH hyx hxx' with ⟨y', hyy', hx'y'⟩
    exact ⟨y', hyy', hx'y'⟩

def RelComp
    {W1 : Type u} {W2 : Type v} {W3 : Type w}
    (Z12 : W1 -> W2 -> Prop)
    (Z23 : W2 -> W3 -> Prop) :
    W1 -> W3 -> Prop :=
  fun x z => exists y, Z12 x y /\ Z23 y z

theorem compose_is_bisimulation
    {W1 : Type u} {W2 : Type v} {W3 : Type w} {Atom : Type x}
    {M1 : Model W1 Atom} {M2 : Model W2 Atom} {M3 : Model W3 Atom}
    {Z12 : W1 -> W2 -> Prop} {Z23 : W2 -> W3 -> Prop}
    (h12 : IsBisimulation M1 M2 Z12)
    (h23 : IsBisimulation M2 M3 Z23) :
    IsBisimulation M1 M3 (RelComp Z12 Z23) := by
  constructor
  · intro x z hxz a
    rcases hxz with ⟨y, hxy, hyz⟩
    exact (h12.atom hxy a).trans (h23.atom hyz a)
  · intro x z hxz x' hxx'
    rcases hxz with ⟨y, hxy, hyz⟩
    rcases h12.forthG hxy hxx' with ⟨y', hyy', hx'y'⟩
    rcases h23.forthG hyz hyy' with ⟨z', hzz', hy'z'⟩
    exact ⟨z', hzz', ⟨y', hx'y', hy'z'⟩⟩
  · intro x z hxz z' hzz'
    rcases hxz with ⟨y, hxy, hyz⟩
    rcases h23.backG hyz hzz' with ⟨y', hyy', hy'z'⟩
    rcases h12.backG hxy hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', ⟨y', hx'y', hy'z'⟩⟩
  · intro x z hxz x' hxx'
    rcases hxz with ⟨y, hxy, hyz⟩
    rcases h12.forthD hxy hxx' with ⟨y', hyy', hx'y'⟩
    rcases h23.forthD hyz hyy' with ⟨z', hzz', hy'z'⟩
    exact ⟨z', hzz', ⟨y', hx'y', hy'z'⟩⟩
  · intro x z hxz z' hzz'
    rcases hxz with ⟨y, hxy, hyz⟩
    rcases h23.backD hyz hzz' with ⟨y', hyy', hy'z'⟩
    rcases h12.backD hxy hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', ⟨y', hx'y', hy'z'⟩⟩
  · intro x z hxz x' hxx'
    rcases hxz with ⟨y, hxy, hyz⟩
    rcases h12.forthH hxy hxx' with ⟨y', hyy', hx'y'⟩
    rcases h23.forthH hyz hyy' with ⟨z', hzz', hy'z'⟩
    exact ⟨z', hzz', ⟨y', hx'y', hy'z'⟩⟩
  · intro x z hxz z' hzz'
    rcases hxz with ⟨y, hxy, hyz⟩
    rcases h23.backH hyz hzz' with ⟨y', hyy', hy'z'⟩
    rcases h12.backH hxy hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', ⟨y', hx'y', hy'z'⟩⟩

def Bisimilar
    {W : Type u} {Atom : Type v}
    (M : Model W Atom) (x y : W) : Prop :=
  exists Z : W -> W -> Prop, IsBisimulation M M Z /\ Z x y

theorem bisimilar_refl
    {W : Type u} {Atom : Type v}
    (M : Model W Atom) :
    forall x, Bisimilar M x x := by
  intro x
  exact ⟨IdRel, identity_is_bisimulation M, rfl⟩

theorem bisimilar_symm
    {W : Type u} {Atom : Type v}
    {M : Model W Atom} {x y : W} :
    Bisimilar M x y -> Bisimilar M y x := by
  intro h
  rcases h with ⟨Z, hZ, hxy⟩
  exact ⟨Converse Z, converse_is_bisimulation hZ, hxy⟩

theorem bisimilar_trans
    {W : Type u} {Atom : Type v}
    {M : Model W Atom} {x y z : W} :
    Bisimilar M x y -> Bisimilar M y z -> Bisimilar M x z := by
  intro hxy hyz
  rcases hxy with ⟨Z1, hZ1, hx1⟩
  rcases hyz with ⟨Z2, hZ2, h2z⟩
  exact ⟨RelComp Z1 Z2, compose_is_bisimulation hZ1 hZ2,
    ⟨y, hx1, h2z⟩⟩

theorem bisimilarity_is_bisimulation
    {W : Type u} {Atom : Type v}
    (M : Model W Atom) :
    IsBisimulation M M (Bisimilar M) := by
  constructor
  · intro x y hxy a
    rcases hxy with ⟨Z, hZ, hZxy⟩
    exact hZ.atom hZxy a
  · intro x y hxy x' hxx'
    rcases hxy with ⟨Z, hZ, hZxy⟩
    rcases hZ.forthG hZxy hxx' with ⟨y', hyy', hx'y'⟩
    exact ⟨y', hyy', ⟨Z, hZ, hx'y'⟩⟩
  · intro x y hxy y' hyy'
    rcases hxy with ⟨Z, hZ, hZxy⟩
    rcases hZ.backG hZxy hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', ⟨Z, hZ, hx'y'⟩⟩
  · intro x y hxy x' hxx'
    rcases hxy with ⟨Z, hZ, hZxy⟩
    rcases hZ.forthD hZxy hxx' with ⟨y', hyy', hx'y'⟩
    exact ⟨y', hyy', ⟨Z, hZ, hx'y'⟩⟩
  · intro x y hxy y' hyy'
    rcases hxy with ⟨Z, hZ, hZxy⟩
    rcases hZ.backD hZxy hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', ⟨Z, hZ, hx'y'⟩⟩
  · intro x y hxy x' hxx'
    rcases hxy with ⟨Z, hZ, hZxy⟩
    rcases hZ.forthH hZxy hxx' with ⟨y', hyy', hx'y'⟩
    exact ⟨y', hyy', ⟨Z, hZ, hx'y'⟩⟩
  · intro x y hxy y' hyy'
    rcases hxy with ⟨Z, hZ, hZxy⟩
    rcases hZ.backH hZxy hyy' with ⟨x', hxx', hx'y'⟩
    exact ⟨x', hxx', ⟨Z, hZ, hx'y'⟩⟩

theorem bisimulation_refines_bisimilarity
    {W : Type u} {Atom : Type v}
    {M : Model W Atom} {Z : W -> W -> Prop}
    (hZ : IsBisimulation M M Z) :
    forall {x y}, Z x y -> Bisimilar M x y := by
  intro x y hxy
  exact ⟨Z, hZ, hxy⟩

def bisimilarityDynamicEquiv
    {W : Type u} {Atom : Type v}
    (M : Model W Atom) :
    DynamicEquiv M (Bisimilar M) where
  refl := bisimilar_refl M
  symm := bisimilar_symm
  trans := bisimilar_trans
  bisim := bisimilarity_is_bisimulation M

theorem dynamicEquiv_refines_bisimilarity
    {W : Type u} {Atom : Type v}
    {M : Model W Atom} {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) :
    forall {x y}, E x y -> Bisimilar M x y := by
  exact bisimulation_refines_bisimilarity hE.bisim

def bisimilaritySetoid
    {W : Type u} {Atom : Type v}
    (M : Model W Atom) : Setoid W where
  r := Bisimilar M
  iseqv := ⟨bisimilar_refl M, bisimilar_symm, bisimilar_trans⟩

def BisimQuot
    {W : Type u} {Atom : Type v}
    (M : Model W Atom) :=
  Quotient (bisimilaritySetoid M)

def bisimilarityPresentation
    {W : Type u} {Atom : Type v}
    (M : Model W Atom) :
    QuotientPresentation W (BisimQuot M) (Bisimilar M) where
  classOf := fun x => Quotient.mk (bisimilaritySetoid M) x
  surj := by
    intro q
    refine Quotient.inductionOn q ?_
    intro x
    exact ⟨x, rfl⟩
  class_eq_iff := by
    intro x y
    constructor
    · intro h
      exact Quotient.exact h
    · intro h
      exact Quotient.sound h

theorem bisimilarity_quotient_invariance
    {W : Type u} {Atom : Type v}
    (M : Model W Atom)
    (phi : Formula Atom) (x : W) :
    Satisfies M x phi <->
      Satisfies
        (quotientModel M (bisimilarityPresentation M))
        ((bisimilarityPresentation M).classOf x)
        phi := by
  exact quotient_invariance
    (bisimilarityDynamicEquiv M)
    (bisimilarityPresentation M)
    phi x

theorem bisimilarity_quotient_is_coarsest_dynamic_safe
    {W : Type u} {Atom : Type v}
    {M : Model W Atom}
    {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) :
    forall {x y},
      E x y ->
      (bisimilarityPresentation M).classOf x =
        (bisimilarityPresentation M).classOf y := by
  intro x y hxy
  exact (bisimilarityPresentation M).class_eq_iff.mpr
    (dynamicEquiv_refines_bisimilarity hE hxy)

end CPOG
