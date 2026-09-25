import CPOG.General

/-!
Modal preservation for the G/D/H fragment of CPOG.

A bounded morphism (atom preservation + forth/back for all three accessibility
relations) preserves every formula in the tri-modal propositional language.
This is the formal bridge from static state abstraction to a dynamically safe
modal abstraction.
-/

namespace CPOG.ModalPreservation

universe uW uQ uA

structure Model (W : Type uW) (Atom : Type uA) where
  G : W -> W -> Prop
  D : W -> W -> Prop
  H : W -> W -> Prop
  val : W -> Atom -> Prop

inductive Formula (Atom : Type uA) where
  | atom : Atom -> Formula Atom
  | bot : Formula Atom
  | imp : Formula Atom -> Formula Atom -> Formula Atom
  | boxG : Formula Atom -> Formula Atom
  | boxD : Formula Atom -> Formula Atom
  | boxH : Formula Atom -> Formula Atom

def Sat {W : Type uW} {Atom : Type uA}
    (M : Model W Atom) (w : W) : Formula Atom -> Prop
  | .atom a => M.val w a
  | .bot => False
  | .imp phi psi => Sat M w phi -> Sat M w psi
  | .boxG phi => forall v, M.G w v -> Sat M v phi
  | .boxD phi => forall v, M.D w v -> Sat M v phi
  | .boxH phi => forall v, M.H w v -> Sat M v phi

structure BoundedMorphism
    {W : Type uW} {Q : Type uQ} {Atom : Type uA}
    (M : Model W Atom) (N : Model Q Atom) (q : W -> Q) : Prop where
  atom : forall w a, M.val w a <-> N.val (q w) a

  forthG : forall {x y}, M.G x y -> N.G (q x) (q y)
  backG : forall {x z}, N.G (q x) z -> exists y, M.G x y /\ q y = z

  forthD : forall {x y}, M.D x y -> N.D (q x) (q y)
  backD : forall {x z}, N.D (q x) z -> exists y, M.D x y /\ q y = z

  forthH : forall {x y}, M.H x y -> N.H (q x) (q y)
  backH : forall {x z}, N.H (q x) z -> exists y, M.H x y /\ q y = z

theorem sat_iff_of_boundedMorphism
    {W : Type uW} {Q : Type uQ} {Atom : Type uA}
    {M : Model W Atom} {N : Model Q Atom} {q : W -> Q}
    (hm : BoundedMorphism M N q) :
    forall (phi : Formula Atom) (w : W), Sat M w phi <-> Sat N (q w) phi := by
  intro phi
  induction phi with
  | atom a =>
      intro w
      exact hm.atom w a
  | bot =>
      intro w
      rfl
  | imp phi psi ihPhi ihPsi =>
      intro w
      constructor
      · intro hImp hQPhi
        have hPhi : Sat M w phi := (ihPhi w).mpr hQPhi
        have hPsi : Sat M w psi := hImp hPhi
        exact (ihPsi w).mp hPsi
      · intro hImp hPhi
        have hQPhi : Sat N (q w) phi := (ihPhi w).mp hPhi
        have hQPsi : Sat N (q w) psi := hImp hQPhi
        exact (ihPsi w).mpr hQPsi
  | boxG phi ih =>
      intro w
      constructor
      · intro hBox z hQ
        rcases hm.backG hQ with ⟨y, hM, hqy⟩
        rw [← hqy]
        exact (ih y).mp (hBox y hM)
      · intro hBox y hM
        have hQ : N.G (q w) (q y) := hm.forthG hM
        exact (ih y).mpr (hBox (q y) hQ)
  | boxD phi ih =>
      intro w
      constructor
      · intro hBox z hQ
        rcases hm.backD hQ with ⟨y, hM, hqy⟩
        rw [← hqy]
        exact (ih y).mp (hBox y hM)
      · intro hBox y hM
        have hQ : N.D (q w) (q y) := hm.forthD hM
        exact (ih y).mpr (hBox (q y) hQ)
  | boxH phi ih =>
      intro w
      constructor
      · intro hBox z hQ
        rcases hm.backH hQ with ⟨y, hM, hqy⟩
        rw [← hqy]
        exact (ih y).mp (hBox y hM)
      · intro hBox y hM
        have hQ : N.H (q w) (q y) := hm.forthH hM
        exact (ih y).mpr (hBox (q y) hQ)

theorem truth_preserved_under_dynamic_abstraction
    {W : Type uW} {Q : Type uQ} {Atom : Type uA}
    {M : Model W Atom} {N : Model Q Atom} {q : W -> Q}
    (hm : BoundedMorphism M N q)
    (phi : Formula Atom) (w : W) :
    Sat M w phi <-> Sat N (q w) phi :=
  sat_iff_of_boundedMorphism hm phi w

end CPOG.ModalPreservation
