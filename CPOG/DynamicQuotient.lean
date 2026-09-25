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

abbrev DynQuotient
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M) :=
  Quotient (dynSetoid B)

def quotientMap
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M) (x : W) : DynQuotient B :=
  Quotient.mk (dynSetoid B) x

theorem quotientMap_eq_iff
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M) (x y : W) :
    quotientMap B x = quotientMap B y <-> B.E x y := by
  constructor
  · intro h
    exact Quotient.exact h
  · intro h
    change Quotient.mk (dynSetoid B) x = Quotient.mk (dynSetoid B) y
    exact Quotient.sound h

def quotientVal
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M) : DynQuotient B -> Atom -> Prop :=
  Quotient.lift (fun x => M.val x) (by
    intro x y hxy
    funext a
    exact propext (B.atom hxy a))

def quotientRel
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M)
    (R : W -> W -> Prop) :
    DynQuotient B -> DynQuotient B -> Prop :=
  fun u v =>
    exists x y,
      quotientMap B x = u /\
      quotientMap B y = v /\
      R x y

def quotientModel
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M) : Model (DynQuotient B) Atom where
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


/-- Equality in the dynamic quotient can only identify states with the same preserved label. -/
theorem quotientMap_preserves_label
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M)
    {C : Type} (first : W -> Option C)
    (hlabel : forall {x y}, B.E x y -> first x = first y) :
    forall x y, quotientMap B x = quotientMap B y -> first x = first y := by
  intro x y hq
  exact hlabel ((quotientMap_eq_iff B x y).1 hq)

/--
Paper Theorem 2B on an actual dynamic quotient: if the chosen dynamic equivalence
preserves FirstCommit labels, distinct persistent FirstCommit branches still refute .2
after quotienting.
-/
theorem firstCommit_dotTwo_fails_on_dynamicQuotient
    {W : Type uW} {Atom : Type uA} {M : Model W Atom}
    (B : DynamicEquivalence M)
    {C : Type}
    (first : W -> Option C)
    (root a b : W) (ca cb : C)
    (hc : ca ≠ cb)
    (hrootA : M.G root a) (hrootB : M.G root b)
    (hfirstA : first a = some ca) (hfirstB : first b = some cb)
    (hpersist : forall {x y : W} {c : C}, M.G x y -> first x = some c -> first y = some c)
    (hlabel : forall {x y}, B.E x y -> first x = first y) :
    Not (CPOG.EpistemicPotentialism.DotTwoR
      (CPOG.EpistemicPotentialism.AbstractRel M.G (quotientMap B))
      (CPOG.EpistemicPotentialism.AbstractFirstCommit (quotientMap B) first ca)
      (quotientMap B root)) := by
  apply CPOG.EpistemicPotentialism.not_dotTwo_of_persistent_split
    (CPOG.EpistemicPotentialism.AbstractRel M.G (quotientMap B))
    (CPOG.EpistemicPotentialism.AbstractFirstCommit (quotientMap B) first ca)
    (quotientMap B root) (quotientMap B a) (quotientMap B b)
  · exact ⟨root, a, rfl, rfl, hrootA⟩
  · exact ⟨root, b, rfl, rfl, hrootB⟩
  · intro z haz
    rcases haz with ⟨s, t, hs, ht, hst⟩
    have hsa : first s = first a :=
      hlabel ((quotientMap_eq_iff B s a).1 hs)
    have hsc : first s = some ca := hsa.trans hfirstA
    have htc : first t = some ca := hpersist hst hsc
    exact ⟨t, ht, htc⟩
  · intro z hbz hhas
    rcases hbz with ⟨s, t, hs, ht, hst⟩
    rcases hhas with ⟨u, hu, huc⟩
    have hsb : first s = first b :=
      hlabel ((quotientMap_eq_iff B s b).1 hs)
    have hsbc : first s = some cb := hsb.trans hfirstB
    have htbc : first t = some cb := hpersist hst hsbc
    have htu : quotientMap B t = quotientMap B u := ht.trans hu.symm
    have hlabels : first t = first u :=
      hlabel ((quotientMap_eq_iff B t u).1 htu)
    have hcodes : some cb = some ca := htbc.symm.trans (hlabels.trans huc)
    exact hc (Option.some.inj hcodes).symm

end CPOG.DynamicQuotient
