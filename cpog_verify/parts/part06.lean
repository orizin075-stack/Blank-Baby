  | diaH phi ih =>
      intro x y hxy
      constructor
      · intro hx
        rcases hx with ⟨x', hxx', hphi⟩
        rcases hZ.forthH hxy hxx' with ⟨y', hyy', hx'y'⟩
        exact ⟨y', hyy', (ih hx'y').mp hphi⟩
      · intro hy
        rcases hy with ⟨y', hyy', hphi⟩
        rcases hZ.backH hxy hyy' with ⟨x', hxx', hx'y'⟩
        exact ⟨x', hxx', (ih hx'y').mpr hphi⟩

end CPOG


namespace CPOG

universe u v w x

variable {I : Type u} {X : Type v} {Y : Type w}


def ObsEq (O : I -> X -> Y) (x y : X) : Prop :=
  forall i, O i x = O i y

theorem obsEq_refl (O : I -> X -> Y) : forall x, ObsEq O x x := by
  intro x i
  rfl

theorem obsEq_symm (O : I -> X -> Y) :
    forall {x y}, ObsEq O x y -> ObsEq O y x := by
  intro x y h i
  exact Eq.symm (h i)

theorem obsEq_trans (O : I -> X -> Y) :
    forall {x y z}, ObsEq O x y -> ObsEq O y z -> ObsEq O x z := by
  intro x y z hxy hyz i
  exact Eq.trans (hxy i) (hyz i)


theorem semantic_minimal_quotient
    (O : I -> X -> Y) (E : X -> X -> Prop)
    (hPres : forall {x y}, E x y -> forall i, O i x = O i y) :
    forall {x y}, E x y -> ObsEq O x y := by
  intro x y hE i
  exact hPres hE i

variable {W : Type u} {Q : Type v} {Atom : Type w}


structure DynamicEquiv (M : Model W Atom) (E : W -> W -> Prop) : Prop where
  refl : forall x, E x x
  symm : forall {x y}, E x y -> E y x
  trans : forall {x y z}, E x y -> E y z -> E x z
  bisim : IsBisimulation M M E


structure QuotientPresentation (W : Type u) (Q : Type v) (E : W -> W -> Prop) where
  classOf : W -> Q
  surj : forall q, exists w, classOf w = q
  class_eq_iff : forall {x y}, classOf x = classOf y <-> E x y

def quotientVal
    (M : Model W Atom) (P : QuotientPresentation W Q E)
    (q : Q) (a : Atom) : Prop :=
  exists x, P.classOf x = q /\ M.val x a

def quotientRel
    (P : QuotientPresentation W Q E) (R : Rel W) : Rel Q :=
  fun q r => exists x y,
    P.classOf x = q /\ P.classOf y = r /\ R x y

def quotientModel
    (M : Model W Atom) (P : QuotientPresentation W Q E) : Model Q Atom where
  val := quotientVal M P
  rG := quotientRel P M.rG
  rD := quotientRel P M.rD
  rH := quotientRel P M.rH

def ProjectionRel (P : QuotientPresentation W Q E) : W -> Q -> Prop :=
  fun x q => P.classOf x = q

private theorem projection_atom
    {M : Model W Atom} {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) (P : QuotientPresentation W Q E)
    {x : W} {q : Q} (hxq : P.classOf x = q) (a : Atom) :
    M.val x a <-> quotientVal M P q a := by
  constructor
  · intro hx
    exact ⟨x, hxq, hx⟩
  · intro hq
    rcases hq with ⟨y, hyq, hy⟩
    have hClasses : P.classOf x = P.classOf y := by
      exact Eq.trans hxq (Eq.symm hyq)
    have hxy : E x y := (P.class_eq_iff).mp hClasses
    exact (hE.bisim.atom hxy a).mpr hy

private theorem projection_forth
    {E : W -> W -> Prop}
    (P : QuotientPresentation W Q E)
    (R : Rel W) {x : W} {q : Q}
    (hxq : P.classOf x = q) {x' : W} (hxx' : R x x') :
    exists q', quotientRel P R q q' /\ P.classOf x' = q' := by
  refine ⟨P.classOf x', ?_, rfl⟩
  exact ⟨x, x', hxq, rfl, hxx'⟩

private theorem projection_back
    {M : Model W Atom} {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) (P : QuotientPresentation W Q E)
    (R : Rel W)
    (back : forall {a b}, E a b -> forall {b'}, R b b' ->
      exists a', R a a' /\ E a' b')
    {x : W} {q q' : Q} (hxq : P.classOf x = q)
    (hqq' : quotientRel P R q q') :
    exists x', R x x' /\ P.classOf x' = q' := by
  rcases hqq' with ⟨a, b, haq, hbq', hab⟩
  have hClass : P.classOf x = P.classOf a := Eq.trans hxq (Eq.symm haq)
  have hxa : E x a := (P.class_eq_iff).mp hClass
  rcases back hxa hab with ⟨x', hxx', hx'b⟩
  have hClassXB : P.classOf x' = P.classOf b := (P.class_eq_iff).mpr hx'b
  exact ⟨x', hxx', Eq.trans hClassXB hbq'⟩

theorem projection_is_bisimulation
    {M : Model W Atom} {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) (P : QuotientPresentation W Q E) :
    IsBisimulation M (quotientModel M P) (ProjectionRel P) := by
  constructor
  · intro x q hxq a
    exact projection_atom hE P hxq a
  · intro x q hxq x' hxx'
    exact projection_forth P M.rG hxq hxx'
  · intro x q hxq q' hqq'
    exact projection_back hE P M.rG hE.bisim.backG hxq hqq'
  · intro x q hxq x' hxx'
    exact projection_forth P M.rD hxq hxx'
  · intro x q hxq q' hqq'
    exact projection_back hE P M.rD hE.bisim.backD hxq hqq'
  · intro x q hxq x' hxx'
    exact projection_forth P M.rH hxq hxx'
  · intro x q hxq q' hqq'
    exact projection_back hE P M.rH hE.bisim.backH hxq hqq'

theorem quotient_invariance
    {M : Model W Atom} {E : W -> W -> Prop}
    (hE : DynamicEquiv M E) (P : QuotientPresentation W Q E)
    (phi : Formula Atom) (x : W) :
    Satisfies M x phi <->
      Satisfies (quotientModel M P) (P.classOf x) phi := by
  exact bisimulation_invariance (projection_is_bisimulation hE P) phi rfl


theorem atom_difference_blocks_bisimulation
    {M : Model W Atom} {Z : W -> W -> Prop}
    (hZ : IsBisimulation M M Z) {x y : W} {a : Atom}
    (hx : M.val x a) (hy : Not (M.val y a)) :
    Not (Z x y) := by
  intro hxy
  exact hy ((hZ.atom hxy a).mp hx)

end CPOG


namespace CPOG

universe u

variable {Q : Type u}

inductive FCAtom where
  | pA

deriving DecidableEq

def fcId : Rel FCWorld := fun x y => x = y

def fcModel : Model FCWorld FCAtom where
  val := fun w _ => PA w
  rG := fcR
  rD := fcId
  rH := fcR
