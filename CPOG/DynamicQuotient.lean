import CPOG.ModalPreservation

namespace CPOG.DynamicQuotient

open CPOG.ModalPreservation

universe uW uA

structure DynamicEquivalence
    {W : Type uW} {Atom : Type uA} (M : Model W Atom) where
  E : W -> W -> Prop
  equiv : Equivalence E
  atom : forall {x y}, E x y -> forall a, M.val x a <-> M.val y a

  forthG : forall {x y x'}, E x y -> M.G x x' ->
    exists y', M.G y y' /\ E x' y'
  backG : forall {x y y'}, E x y -> M.G y y' ->
    exists x', M.G x x' /\ E x' y'

  forthD : forall {x y x'}, E x y -> M.D x x' ->
    exists y', M.D y y' /\ E x' y'
  backD : forall {x y y'}, E x y -> M.D y y' ->
    exists x', M.D x x' /\ E x' y'

  forthH : forall {x y x'}, E x y -> M.H x x' ->
    exists y', M.H y y' /\ E x' y'
  backH : forall {x y y'}, E x y -> M.H y y' ->
    exists x', M.H x x' /\ E x' y'

def dynSetoid
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M) : Setoid W where
  r := B.E
  iseqv := B.equiv

abbrev DynamicQuotient
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M) :=
  Quotient (dynSetoid B)

def quotientMap
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M) (x : W) : DynamicQuotient B :=
  Quotient.mk (dynSetoid B) x

theorem quotientMap_eq_iff
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M) (x y : W) :
    quotientMap B x = quotientMap B y <-> B.E x y := by
  constructor
  · exact Quotient.exact
  · exact Quotient.sound

def quotientVal
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M) : DynamicQuotient B -> Atom -> Prop :=
  Quotient.lift (fun x => M.val x) (by
    intro x y hxy
    funext a
    exact propext (B.atom hxy a))

def quotientRel
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M)
    (R : W -> W -> Prop) :
    DynamicQuotient B -> DynamicQuotient B -> Prop :=
  fun u v =>
    exists x y,
      quotientMap B x = u /\
      quotientMap B y = v /\
      R x y

def quotientModel
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M) : Model (DynamicQuotient B) Atom where
  G := quotientRel B M.G
  D := quotientRel B M.D
  H := quotientRel B M.H
  val := quotientVal B

theorem quotientMap_surjective
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M) :
    Function.Surjective (quotientMap B) := by
  intro q
  refine Quotient.inductionOn q ?_
  intro x
  exact ⟨x, rfl⟩

theorem quotientMap_boundedMorphism
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M) :
    BoundedMorphism M (quotientModel B) (quotientMap B) := by
  refine {
    atom := ?_
    forthG := ?_
    backG := ?_
    forthD := ?_
    backD := ?_
    forthH := ?_
    backH := ?_
  }
  · intro w a
    rfl
  · intro x y hxy
    exact ⟨x, y, rfl, rfl, hxy⟩
  · intro x z hq
    rcases hq with ⟨x', y', hx, hy, hxy⟩
    have hE : B.E x' x := Quotient.exact hx
    rcases B.forthG hE hxy with ⟨y, hGy, hEy⟩
    refine ⟨y, hGy, ?_⟩
    have hqq : quotientMap B y' = quotientMap B y := Quotient.sound hEy
    exact hqq.symm.trans hy
  · intro x y hxy
    exact ⟨x, y, rfl, rfl, hxy⟩
  · intro x z hq
    rcases hq with ⟨x', y', hx, hy, hxy⟩
    have hE : B.E x' x := Quotient.exact hx
    rcases B.forthD hE hxy with ⟨y, hDy, hEy⟩
    refine ⟨y, hDy, ?_⟩
    have hqq : quotientMap B y' = quotientMap B y := Quotient.sound hEy
    exact hqq.symm.trans hy
  · intro x y hxy
    exact ⟨x, y, rfl, rfl, hxy⟩
  · intro x z hq
    rcases hq with ⟨x', y', hx, hy, hxy⟩
    have hE : B.E x' x := Quotient.exact hx
    rcases B.forthH hE hxy with ⟨y, hHy, hEy⟩
    refine ⟨y, hHy, ?_⟩
    have hqq : quotientMap B y' = quotientMap B y := Quotient.sound hEy
    exact hqq.symm.trans hy

theorem dynamicQuotient_preserves_all_formulas
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M)
    (phi : Formula Atom) (w : W) :
    Sat M w phi <-> Sat (quotientModel B) (quotientMap B w) phi := by
  exact sat_iff_of_boundedMorphism (quotientMap_boundedMorphism B) phi w

end CPOG.DynamicQuotient
